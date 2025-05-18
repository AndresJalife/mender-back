import os

import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors

from src.config.database import Database, get_db
from src.model import dto
from src.models import UserPostInfo, Entity, CalculatedRating, EntityGenre
from src.service.ImplicitService import ImplicitService
from src.service.Logger import logger


def get_user_ratings(db, user_id):
    ratings_and_ids = (
        db.query(UserPostInfo.user_rating, Entity.tmbd_id)
        .join(Entity, UserPostInfo.post_id == Entity.entity_id)
        .filter(UserPostInfo.user_id == user_id)
        .order_by(UserPostInfo.created_date.desc())
        .limit(5)
        .all()
    )

    return [(rating[1], rating[0]) for rating in ratings_and_ids]


def get_seen_movies(db, user_id):
    posts = (
        db.query(UserPostInfo, Entity)
        .join(Entity, UserPostInfo.post_id == Entity.entity_id)
        .filter(UserPostInfo.user_id == user_id)
        .filter(UserPostInfo.seen == True)
        .all()
    )

    return [entity.tmbd_id for user_post, entity in posts]


def get_user_implicit_ratings(db, user_id):
    implicit_ratings = (
        db.query(CalculatedRating.rating, CalculatedRating.post_id)
        .join(Entity, Entity.entity_id == CalculatedRating.post_id)
        .filter(CalculatedRating.user_id == user_id)
        .order_by(CalculatedRating.updated_date.desc())
        .limit(25)
    )

    return [(rating[1], rating[0]) for rating in implicit_ratings]

def get_filtered_movies_ids(db, filters: dto.PostFilters, movie_ids):
    query = db.query(Entity).join(EntityGenre).filter(Entity.tmbd_id.in_(movie_ids))

    # Genre
    if filters.genre:
        query = query.filter(EntityGenre.name == filters.genre)
    # Release date
    if filters.min_release_date:
        query = query.filter(Entity.release_date >= filters.min_release_date)
    if filters.max_release_date:
        query = query.filter(Entity.release_date <= filters.max_release_date)
    if filters.avoid_tmdb_ids:
        ids = [id_ for id_ in filters.avoid_tmdb_ids if id_]  # remove empty strings
        if ids:
            query = query.filter(Entity.tmbd_id.notin_(ids))

    # # Actor
    # if filters.actor:
    #     sql_filters.append(Entity.actors == filters.actor)
    # # Director
    # if filters.director:
    #     sql_filters.append(Entity.director == filters.director)

    results = (
        query
        .all()
    )
    #
    # if filters.avoid_imdb_ids:
    #     movie_ids = [entity.tmbd_id for entity in results if id not in filters.avoid_imdb_ids]
    # else:
    #     movie_ids = [entity.tmbd_id for entity in results]

    return [entity.tmbd_id for entity in results]

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

    def get_recommendation(self, user_id, filters, k=10):
        implicit_ratings = get_user_implicit_ratings(self.db, user_id)
        user_ratings = get_user_ratings(self.db, user_id)
        seen_movies = get_seen_movies(self.db, user_id)

        return self.get_recommended_movies(user_ratings, seen_movies, filters, k)


db_instance = next(get_db())
recommendation_service = RecommendationService(db_instance)
