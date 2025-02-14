
class RecommendationService:

    def __init__(self, recommendationRepository):
        self.recommendationRepository = recommendationRepository

    def get_recommendation(self, user_id):
        return self.recommendationRepository.get_recommendation(user_id)

