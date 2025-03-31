import os

import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors

from src.config.database import Database, get_db
from src.service.Logger import logger

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
        kNN = NearestNeighbors(n_neighbors=k + 1, algorithm="brute", metric=metric)
        kNN.fit(self.X)
        distances, indices = kNN.kneighbors(user_vec, return_distance=True)

        similar_users = []
        for i in range(1, k + 1):
            n = indices[0][i]
            user_id = self.user_inv_mapper[n]
            distance = distances[0][i]
            similarity = 1 - distance  # Convert distance to similarity
            similar_users.append((user_id, similarity))

        return similar_users

    def get_recommended_movies(self, rated_movies, k=10):
        """
        Finds movie recommendations based on users with similar preferences to the given rated movies,
        using a weighted average rating approach.

        Args:
            rated_movies: List of tuples (movie_id, rating)
            k: Number of recommendations to return

        Output: List of recommended movie IDs with predicted ratings
        """
        similar_users = self.find_similar_users_to_movies(rated_movies, k=20)
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
        rated_movie_ids = [m[0] for m in rated_movies]

        # Remove movies already rated by input
        movie_predictions = movie_predictions[~movie_predictions.index.isin(rated_movie_ids)]

        # Return top recommendations with predicted ratings
        return movie_predictions.sort_values('predicted_rating', ascending=False).head(k).index.to_list()

    def get_recommendation(self, user_id, k=10):
        ### Hardcode
        user_ratings = [
            (568124, 5),
            (38757, 5),
            (109445, 5),
            (9502, 5),
            (508439, 5)
        ]
        return self.get_recommended_movies(user_ratings, k)

recommendation_service = RecommendationService(get_db())