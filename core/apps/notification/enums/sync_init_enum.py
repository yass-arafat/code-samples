from enum import Enum


class SyncInitType(Enum):
    PAYMENT_INITIAL_SUCCESS = "PAYMENT_INITIAL_SUCCESS"
    PAYMENT_RENEWAL_SUCCESS = "PAYMENT_RENEWAL_SUCCESS"
    PAYMENT_CANCEL_SUCCESS = "PAYMENT_CANCEL_SUCCESS"
    PAYMENT_EXPIRE_SUCCESS = "PAYMENT_EXPIRE_SUCCESS"
    TRIAL_EXPIRE_SUCCESS = "TRIAL_EXPIRE_SUCCESS"

    @classmethod
    def contains(cls, text):
        for x in cls:
            if x.value[0].lower() == text:
                return True
        return False
