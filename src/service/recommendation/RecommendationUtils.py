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

def get_filtered_movies_ids(db, filters: dto.PostFilters, movie_ids):
    query = (db.query(Entity)
             .join(EntityGenre)
             .join(Actor)
             .filter(Entity.tmbd_id.in_(movie_ids)))

    # Genre
    if filters.genres:
        sql_filters = [EntityGenre.name.ilike(f"%{genre}%") for genre in filters.genres]
        if len(sql_filters) == 1:
            query = query.filter(sql_filters[0])
        elif len(sql_filters) > 1:
            query = query.filter(or_(*sql_filters))
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
    if filters.actors:
        sql_filters = [Actor.name.ilike(f"%{actor}%") for actor in filters.actors]
        if len(sql_filters) == 1:
            query = query.filter(sql_filters[0])
        elif len(sql_filters) > 1:
            query = query.filter(or_(*sql_filters))
    # Director
    if filters.directors:
        sql_filters = [Entity.director.ilike(f"%{director}%") for director in filters.directors]
        if len(sql_filters) == 1:
            query = query.filter(sql_filters[0])
        elif len(sql_filters) > 1:
            query = query.filter(or_(*sql_filters))

    # Language
    if filters.original_language:
        query = query.filter(Entity.original_language == filters.original_language)

    # Runtime
    if filters.min_runtime:
        query = query.filter(Entity.runtime >= filters.min_runtime)

    if filters.max_runtime:
        query = query.filter(Entity.runtime <= filters.max_runtime)

    results = (
        query
        .all()
    )

    return [entity.tmbd_id for entity in results]


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