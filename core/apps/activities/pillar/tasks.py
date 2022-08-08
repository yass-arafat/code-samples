from core.apps.activities.pillar.services import ThirdPartyActivityService
from core.apps.common.common_functions import clear_user_cache
from core.apps.user_auth.models import UserAuthModel


# @shared_task
def process_athlete_activity_from_dakghor(athlete_id, activities):
    user_auth = UserAuthModel.objects.filter(id=athlete_id).first()
    ThirdPartyActivityService.process_athlete_activity(user_auth, activities)
    clear_user_cache(user_auth)
