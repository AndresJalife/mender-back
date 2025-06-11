import random
from abc import ABC, abstractmethod

class RecommendationStrategy(ABC):
    @abstractmethod
    def recommend(self, user_ratings, filters, seen_movies, recommendation_service, k):
        pass


class RandomRecommendationStrategy(RecommendationStrategy):
    def recommend(self, user_ratings, filters, seen_movies, recommendation_service, k):
        recommendations = []
        return recommendation_service.get_random_popular_movie(user_ratings, filters, seen_movies, recommendations, k)


class ContentBasedRecommendationStrategy(RecommendationStrategy):
    def recommend(self, user_ratings, filters, seen_movies, recommendation_service, k):
        recommendations = []
        return recommendation_service.get_content_based_recommendation(user_ratings, filters, seen_movies, recommendations, k)


class BestModelStrategy(RecommendationStrategy):
    def recommend(self, user_ratings, filters, seen_movies, recommendation_service, k):
        # Possibly reserve 1 slot for a random recommendation
        reserve_random = random.random() > 0.5
        if reserve_random:
            k -= 1
        recommendations = []
        collaborative_k = int(k * 0.7)
        recommendations += recommendation_service.get_ibcf_recommendation(user_ratings, filters, seen_movies, collaborative_k)
        content_k = k - len(recommendations)
        recommendations += recommendation_service.get_content_based_recommendation(user_ratings, filters, seen_movies, recommendations, content_k)
        if reserve_random:
            recommendations += recommendation_service.get_random_popular_movie(user_ratings, filters, seen_movies, recommendations, 1)
        return recommendations
