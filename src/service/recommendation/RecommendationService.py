import math
import os
import ast
import random
from functools import partial

import pandas as pd
import numpy as np
import pickle
from scipy.sparse import load_npz
from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors
from starlette.concurrency import run_in_threadpool

from src.config.database import Database, get_db
from src.model import dto
from src.service.ImplicitService import ImplicitService
from src.service.Logger import logger
from src.service.recommendation.RecommendationUtils import get_user_implicit_ratings, get_user_ratings, get_seen_movies, get_filtered_df


class RecommendationService:

    def __init__(self, db: Database):
        logger.info(f"Initializing RecommendationService")
        self.db = db
        self.implicit_service = ImplicitService(db)

        with open(os.getenv("MOVIE_MAPPER_PATH"), "rb") as f:
            self.movie_mapper = pickle.load(f)

        with open(os.getenv("MOVIE_INV_MAPPER_PATH"), "rb") as f:
            self.movie_inv_mapper = pickle.load(f)

        with open(os.getenv("USER_INV_MAPPER_PATH"), "rb") as f:
            self.user_inv_mapper = pickle.load(f)

        self.X = load_npz(os.getenv("SPARSE_X_PATH"))

        self.item_similarity = load_npz(os.getenv("ITEM_SIMILARITY_PATH"))

        # Init for content-based-recommendation
        self.movies_similarity = pd.read_csv(os.getenv("MOVIES_PATH"))
        self.movies_similarity.set_index('index', inplace=True)
        self.movies_similarity.index.name = None
        self.movies_similarity['genres'] = self.movies_similarity['genres'].apply(ast.literal_eval)
        self.movies_similarity['actors'] = self.movies_similarity['actors'].apply(ast.literal_eval)

        self.knn_columns = ['vote_average', 'revenue', 'runtime', 'budget', 'popularity', 'en',
                       'ja', 'fr', 'es', 'de', 'it', 'zh', 'ko', 'years_since_release',
                       'Action', 'Adventure', 'Animation', 'Comedy', 'Crime', 'Documentary',
                       'Drama', 'Family', 'Fantasy', 'History', 'Horror', 'Music', 'Mystery',
                       'Romance', 'Science Fiction', 'TV Movie', 'Thriller', 'War', 'Western']

        logger.info(f"RecommendationService initialized")

    def get_ibcf_recommendation(self, user_ratings, filters, seen_movies, k=10):
        num_items = self.item_similarity.shape[0]
        user_vector = np.zeros((1, num_items))

        rated_indices = []
        for movie_id, rating in user_ratings:
            if movie_id in self.movie_mapper:
                idx = self.movie_mapper[movie_id]
                user_vector[0, idx] = rating - 3
                rated_indices.append(idx)

        if np.count_nonzero(user_vector) == 0:
            return []

        user_vector = csr_matrix(user_vector)
        predicted_scores = user_vector.dot(self.item_similarity)  # shape (1, num_items)

        # Get allowed ids according to filters
        rated_movies = [movie_id for movie_id, _ in user_ratings]
        allowed_ids = get_filtered_df(self.movies_similarity[~self.movies_similarity.index.isin(rated_movies)], filters, seen_movies, recommendations=[])

        # Set non available ids prediction to 0
        for i in range(predicted_scores.shape[1]):
            movie_id = self.movie_inv_mapper[i]
            if movie_id not in allowed_ids:
                predicted_scores[0, i] = 0

        top_k_idx = np.argpartition(-predicted_scores.toarray()[0], k)[:k]
        top_k_idx = top_k_idx[np.argsort(-predicted_scores.toarray()[0][top_k_idx])]

        return [self.movie_inv_mapper[i] for i in top_k_idx]

    def get_content_based_recommendation(self, user_ratings, filters, seen_movies, recommendations, k=10):
        # 1. Find the highest rating in the user_ratings
        max_rating = max(rating for _, rating in user_ratings)

        if max_rating < 4:
            return []

        # 2. Get all movie_ids with that max rating
        top_movies = [movie_id for movie_id, rating in user_ratings if rating > max_rating - 0.3]

        if len(top_movies) * 3 < k:
            top_k_per_movie = math.ceil(k / len(top_movies))
        else:
            top_k_per_movie = 3

        # Prepare the NearestNeighbors model
        nn = NearestNeighbors(n_neighbors=top_k_per_movie, algorithm='auto', metric='cosine')

        # Will hold tuples: (movie_id, distance, source_movie_id)
        all_candidates = []

        # Filter movies
        rated_movies = [movie_id for movie_id, _ in user_ratings]
        knn_df = get_filtered_df(self.movies_similarity[~self.movies_similarity.index.isin(rated_movies)], filters, seen_movies, recommendations)

        for movie_id in top_movies:
            if movie_id not in self.movies_similarity.index:
                continue

            # Fit the model on available movies
            nn.fit(knn_df[self.knn_columns])

            # Query vector of the target movie
            target_vector = self.movies_similarity.loc[movie_id, self.knn_columns].values.reshape(1, -1)

            distances, indices = nn.kneighbors(target_vector, n_neighbors=top_k_per_movie)

            # Get recommended movie IDs
            recommended_ids = knn_df.iloc[indices[0]].index

            # Store (movie, distance, source movie)
            for rec_id, dist in zip(recommended_ids, distances[0]):
                all_candidates.append((rec_id, dist, movie_id))

        # 3. Sort all candidates by distance ascending (closest first)
        all_candidates.sort(key=lambda x: x[1])

        # 4. Keep unique recommended movies but only top final_k globally by distance
        recommended_movies = []
        seen = set()
        for movie_id, dist, source_movie in all_candidates:
            if movie_id not in seen:
                recommended_movies.append(movie_id)
                seen.add(movie_id)
            if len(recommended_movies) == k:
                break

        return recommended_movies

    def get_random_popular_movie(self, user_ratings, filters, seen_movies, recommendations, k=10):
        rated_movies = [movie_id for movie_id, _ in user_ratings]
        df = get_filtered_df(self.movies_similarity[~self.movies_similarity.index.isin(rated_movies)], filters, seen_movies, recommendations)

        df['popularity_score'] = df["popularity"] * df["vote_average"]

        # Normalize scores to sum to 1 for probability sampling
        prob = df["popularity_score"]
        prob = prob / prob.sum()

        # Sample without replacement, using popularity_score as weight
        recommended = df.sample(n=k, weights=prob, replace=False).index.tolist()
        return recommended

    def get_recommendation(self, user_id, filters, k=10):
        implicit_ratings = get_user_implicit_ratings(self.db, user_id)
        user_ratings = get_user_ratings(self.db, user_id)
        seen_movies = get_seen_movies(self.db, user_id)
        # Possibly reserve 1 slot for a random recommendation
        reserve_random = random.random() > 0.5
        recommendation_count = k - 1 if reserve_random else k
        recommendations = []
        collaborative_k = int(k*0.7)
        recommendations += (self.get_ibcf_recommendation(user_ratings, filters, seen_movies, collaborative_k))
        content_k = k - len(recommendations)
        recommendations += (self.get_content_based_recommendation(user_ratings, filters, seen_movies, recommendations, content_k))
        if reserve_random:
            recommendations.append(self.get_random_popular_movie(user_ratings, filters, seen_movies, recommendations, 1))
        return recommendations

    async def get_recommendations_async(self, user_id: int,  filters: dto.PostFilters, k: int = 10) -> list[int]:
        fn = partial(self.get_recommendation, user_id, filters, k)
        return await run_in_threadpool(fn)


db_instance = next(get_db())
# recommendation_service = RecommendationService(db_instance)

recommendation_service = None