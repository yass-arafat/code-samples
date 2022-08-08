from core.apps.common.dictionary.training_zone_dictionary import (
    training_zone_truth_table_dict,
)


def get_week_focus_dictionary(user, week, total_blocks, current_block=None):
    if not current_block:
        current_block = user.user_blocks.filter(
            block_code=week.block_code, is_active=True
        ).last()
    week_focus_dict = {
        "zone_focus": week.zone_focus,
        "focus_name": training_zone_truth_table_dict[week.zone_focus]["zone_name"],
        "week_type": week.week_type,
        "current_block": current_block.number,
        "total_block": total_blocks,
        "start_date": week.start_date,
        "end_date": week.end_date,
    }
    return week_focus_dict
