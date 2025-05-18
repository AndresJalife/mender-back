import os
import ast

import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors

from src.config.database import Database, get_db
from src.model import dto
from src.service.ImplicitService import ImplicitService
from src.service.Logger import logger
from src.service.recommendation.RecommendationUtils import get_filtered_movies_ids, get_user_implicit_ratings, \
    get_user_ratings, get_seen_movies


class RecommendationService:

    def __init__(self, db: Database):
        pass
        logger.info(f"Initializing RecommendationService")
        self.db = db
        self.ratings = pd.read_csv(os.getenv("RATINGS_PATH"))
        self.ratings = self.ratings[['user_id', 'movie_id', 'rating']]
        M = self.ratings['user_id'].nunique()
        N = self.ratings['movie_id'].nunique()

        user_mapper = dict(zip(np.unique(self.ratings["user_id"]), list(range(M))))
        self.movie_mapper = dict(zip(np.unique(self.ratings["movie_id"]), list(range(N))))

        self.user_inv_mapper = dict(zip(list(range(M)), np.unique(self.ratings["user_id"])))

        user_index = [user_mapper[i] for i in self.ratings['user_id']]
        item_index = [self.movie_mapper[i] for i in self.ratings['movie_id']]

        self.X = csr_matrix((self.ratings["rating"], (user_index, item_index)), shape=(M, N))

        self.implicit_service = ImplicitService(db)

        # Init for content-based-recommendation
        self.movies_similarity = pd.read_csv(os.getenv("MOVIES_PATH"))
        self.movies_similarity.set_index('index', inplace=True)
        self.movies_similarity.index.name = None
        self.movies_similarity['genres'] = self.movies_similarity['genres'].apply(ast.literal_eval)
        self.movies_similarity['actors'] = self.movies_similarity['actors'].apply(ast.literal_eval)

        logger.info(f"RecommendationService initialized")

    def find_similar_users_to_movies(self, rated_movies, k=10, metric='cosine'):
        """
        Finds users with similar preferences to the given list of rated movies.

        Args:
            rated_movies: List of tuples (movie_id, rating)
            k: Number of similar users to retrieve
            metric: Distance metric for kNN calculations

        Output: List of similar user IDs
        """
        movie_indices = [self.movie_mapper[movie_id] for movie_id, _ in rated_movies if movie_id in self.movie_mapper]
        if not movie_indices:
            return []

        # Create a user preference vector based on the given rated movies
        user_vec = np.zeros(self.X.shape[1])
        for movie_id, rating in rated_movies:
            if movie_id in self.movie_mapper:
                user_vec[self.movie_mapper[movie_id]] = rating
        user_vec = user_vec.reshape(1, -1)

        # Find similar users
        knn = NearestNeighbors(n_neighbors=k + 1, algorithm="brute", metric=metric)
        knn.fit(self.X)
        distances, indices = knn.kneighbors(user_vec, return_distance=True)

        similar_users = []
        for i in range(1, k + 1):
            n = indices[0][i]
            user_id = self.user_inv_mapper[n]
            distance = distances[0][i]
            similarity = 1 - distance  # Convert distance to similarity
            similar_users.append((user_id, similarity))

        return similar_users

    def get_recommended_movies(self, ratings, seen_movies, filters: dto.PostFilters, k=10):
        """
        Finds movie recommendations based on users with similar preferences to the given rated movies,
        using a weighted average rating approach.

        Args:
            rated_movies: List of tuples (movie_id, rating)
            k: Number of recommendations to return

        Output: List of recommended movie IDs with predicted ratings
        :param ratings:
        :param seen_movies:
        :param filters:
        :param k:
        """
        similar_users = self.find_similar_users_to_movies(ratings, k=20)
        similar_users = pd.DataFrame(similar_users, columns=['user_id', 'similarity'])

        # Get movies rated by similar users
        similar_ratings = self.ratings[self.ratings.user_id.isin(similar_users.user_id.values)]

        # Merge with similarity scores
        merged_ratings = similar_ratings.merge(similar_users, on='user_id', how='inner')

        # Compute weighted rating
        merged_ratings['weighted_rating'] = merged_ratings['rating'] * merged_ratings['similarity']

        # Aggregate ratings per movie
        movie_predictions = merged_ratings.groupby('movie_id').agg(
                predicted_rating=('weighted_rating', 'sum'),
                similarity_sum=('similarity', 'sum')
        )

        # Normalize by total similarity to get final predicted rating
        movie_predictions['predicted_rating'] /= movie_predictions['similarity_sum']
        movie_predictions.drop(columns=['similarity_sum'], inplace=True)

        # Get movie IDs from input list
        ratings_ids = [m[0] for m in ratings]

        # Remove movies already rated by input
        movie_predictions = movie_predictions[~movie_predictions.index.isin(ratings_ids)]
        # Remove movies the user has already seen
        movie_predictions = movie_predictions[~movie_predictions.index.isin(seen_movies)]
        # Apply filters
        movie_predictions = movie_predictions[movie_predictions.index.isin(get_filtered_movies_ids(self.db, filters, movie_predictions.index))]

        # Return top recommendations with predicted ratings
        return movie_predictions.sort_values('predicted_rating', ascending=False).head(k).index.to_list()

    def get_knn_neighbors_from_movie(self, user_ratings, seen_movies, filters: dto.PostFilters, recommendations, k):
        movie_ids = [rating[0] for rating in user_ratings]
        highest_rated_id = max(user_ratings, key=lambda x: x[1])[0]
        target = self.movies_similarity.loc[highest_rated_id]

        # Does not recommend already seen movies and does not recommend already recommended movies
        knn_df = self.movies_similarity[(~self.movies_similarity.index.isin(movie_ids)) &
                               (~self.movies_similarity.index.isin(seen_movies)) &
                               (~self.movies_similarity.index.isin(recommendations))]

        # Apply filters
        if filters.genres:
            knn_df = knn_df[knn_df.genres.apply(
                lambda genres: any(genre in filters.genres for genre in genres)
            )]
        if filters.min_release_date:
            knn_df = knn_df[knn_df.release_date >= filters.min_release_date]
        if filters.max_release_date:
            knn_df = knn_df[knn_df.release_date <= filters.max_release_date]
        if filters.actors:
            knn_df = knn_df[knn_df.actors.apply(
                lambda actors: any(actor in filters.actors for actor in actors)
            )]
        if filters.directors:
            knn_df = knn_df[knn_df.director.isin(filters.directors)]
        if filters.avoid_tmdb_ids:
            knn_df = knn_df[~knn_df.index.isin(filters.avoid_tmdb_ids)]

        # Check if target movie is in the knn_df
        target_in_knn_df = highest_rated_id in knn_df.index

        # Choose number of neighbors
        n_neighbors = min(k + 1 if target_in_knn_df else k, len(knn_df))
        if n_neighbors == 0:
            return [], []

        # Train knn model
        knn_columns = ['vote_average', 'revenue', 'runtime', 'budget', 'popularity', 'en',
                       'ja', 'fr', 'es', 'de', 'it', 'zh', 'ko', 'years_since_release',
                       'Action', 'Adventure', 'Animation', 'Comedy', 'Crime', 'Documentary',
                       'Drama', 'Family', 'Fantasy', 'History', 'Horror', 'Music', 'Mystery',
                       'Romance', 'Science Fiction', 'TV Movie', 'Thriller', 'War', 'Western']
        knn = NearestNeighbors(n_neighbors=6, algorithm='auto', metric='cosine')
        knn.fit(knn_df[knn_columns])

        # Query the model to find the top 5 most similar movies (including the target movie itself)
        distances, indices = knn.kneighbors([target[knn_columns]], n_neighbors=n_neighbors)

        if target_in_knn_df:
            recommended_indices = indices[0][1:]
        else:
            recommended_indices = indices[0]

        return knn_df.index[recommended_indices].to_list()

    def get_content_based_recommendation(self, user_ratings, seen_movies, filters:dto.PostFilters, recommendations, k):

        return self.get_knn_neighbors_from_movie(user_ratings, seen_movies, filters, recommendations, k)

    def get_recommendation(self, user_id, filters, k=10):
        implicit_ratings = get_user_implicit_ratings(self.db, user_id)
        user_ratings = get_user_ratings(self.db, user_id)
        seen_movies = get_seen_movies(self.db, user_id)

        print('USER RATINGS:', user_ratings)

        recommendations = []
        collaborative_k = int(k*0.7)
        recommendations += (self.get_recommended_movies(user_ratings, seen_movies, filters, collaborative_k))
        print('recommendations:', recommendations)
        content_k = k - len(recommendations)
        recommendations += (self.get_content_based_recommendation(user_ratings, seen_movies, filters, recommendations, content_k))
        print('recommendations:', recommendations)
        return recommendations

db_instance = next(get_db())
recommendation_service = RecommendationService(db_instance)
