import logging
import time

import requests

logger = logging.getLogger(__name__)


class UserWahooService:
    @classmethod
    def get_wahoo_user_info(cls, access_token):
        headers = {
            "Authorization": f"Bearer {access_token}",
        }
        url = "https://api.wahooligan.com/v1/user"
        response = requests.get(url, headers=headers)

        logger.info(f"User Wahoo info: {response}")
        return response.json()

    @classmethod
    def get_wahoo_expire_at(cls, wahoo_expire_in):
        expire_in = wahoo_expire_in
        current_time = int(time.time())
        expire_at = current_time + expire_in
        return expire_at
