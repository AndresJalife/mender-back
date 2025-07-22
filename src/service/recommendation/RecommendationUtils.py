from operator import or_

from src.model import dto
from src.models import UserPostInfo, Entity, CalculatedRating, EntityGenre, Actor

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

def get_filtered_df(df, filters, seen_movies, recommendations):
    knn_df = df[(~df.index.isin(seen_movies)) &
                (~df.index.isin(recommendations))].copy()

    # Apply filters
    if filters.genres:
        knn_df = knn_df[knn_df.genres.apply(
            lambda genres: any(genre in filters.genres for genre in genres)
        )]
    if filters.min_release_date:
        knn_df = knn_df[knn_df.release_date >= filters.min_release_date.strftime("%Y-%m-%d")]
    if filters.max_release_date:
        knn_df = knn_df[knn_df.release_date <= filters.max_release_date.strftime("%Y-%m-%d")]
    if filters.actors:
        knn_df = knn_df[knn_df.actors.apply(
            lambda actors: any(actor in filters.actors for actor in actors)
        )]
    if filters.directors:
        knn_df = knn_df[knn_df.director.isin(filters.directors)]
    if filters.avoid_tmdb_ids:
        knn_df = knn_df[~knn_df.index.isin(filters.avoid_tmdb_ids)]
    return knn_df

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