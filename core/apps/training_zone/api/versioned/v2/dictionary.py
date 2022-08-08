def get_zone_boundary_dictionary(zone_no, zone_name, zone_boundary_text):
    return {
        "zone_number": zone_no,
        "zone_name": zone_name,
        "zone_boundary": zone_boundary_text,
    }


def get_training_zone_dictionary(
    current_ftp=None,
    current_fthr=None,
    power_zone_boundaries=None,
    heart_rate_zone_boundaries=None,
):
    return {
        "current_ftp": current_ftp if current_ftp else None,
        "current_fthr": current_fthr if current_fthr else None,
        "power_zone_boundaries": power_zone_boundaries,
        "heart_rate_zone_boundaries": heart_rate_zone_boundaries,
    }
