def timezone_dict(user_profile):
    return {
        "timezone_id": user_profile.timezone.id,
        "timezone_name": user_profile.timezone.name,
        "timezone_offset": user_profile.timezone.offset,
        "timezone_type": user_profile.timezone.type,
    }
