import datetime
from decimal import Decimal

from django.db.models import Q

from core.apps.session.utils import check_if_intervals_repeat


def initialize_send_workout_to_garmin_dict(workout_name, session):
    """Initialize the workout dictionary to send to Garmin"""
    current_date_time = str(datetime.datetime.now()).replace(" ", "T")
    return {
        "workoutName": workout_name,
        "description": session.description,
        "updatedDate": current_date_time,
        "createdDate": current_date_time,
        "sport": "CYCLING",  # Need to modify it when Pillar will support plans for other sports too
        "estimatedDurationInSecs": session.duration_in_minutes * Decimal(60.0),
        "estimatedDistanceInMeters": None,
        "poolLength": None,
        "workoutProvider": "Pillar",
        "poolLengthUnit": None,
    }


def get_repeat_steps_dict(step_order, repeat_value, repeat_steps_list):
    """Returns workout repeat step dictionary according to Garmin defined format"""
    return {
        "type": "WorkoutRepeatStep",
        "stepOrder": step_order,
        "repeatType": "REPEAT_UNTIL_STEPS_CMPLT",
        "repeatValue": repeat_value,
        "steps": repeat_steps_list,
    }


def get_single_step_dict(step_order, session_interval, ftp, fthr, data_type):
    """Returns a single workout step dictionary according to Garmin defined format"""
    from core.apps.garmin.utils import get_interval_target_values, get_step_intensity

    intensity = get_step_intensity(session_interval.name)
    target_value_low, target_value_high = get_interval_target_values(
        ftp, fthr, data_type, session_interval
    )
    return {
        "type": "WorkoutStep",
        "stepOrder": step_order,
        "intensity": intensity,
        "description": None,
        "durationType": "TIME",
        "durationValue": session_interval.time_in_seconds,
        "durationValueType": None,
        "targetType": data_type,
        "targetValue": None,
        "targetValueLow": int(target_value_low),
        "targetValueHigh": int(target_value_high),
        "targetValueType": None,
        "strokeType": None,
        "equipmentType": None,
        "exerciseCategory": None,
        "exerciseName": None,
        "weightValue": None,
        "weightDisplayUnit": None,
    }


def get_workout_steps_dict_for_garmin(data_type, ftp, fthr, planned_session):
    """Return the steps or intervals of a workout"""
    steps = []
    if planned_session.is_pad_applicable:
        session_intervals = planned_session.session.session_intervals.filter(
            Q(time_in_seconds__gt=0) | Q(is_padding_interval=True)
        ).order_by("id")
    else:
        session_intervals = planned_session.session.session_intervals.filter(
            Q(time_in_seconds__gt=0)
        ).order_by("id")

    session_intervals_length = len(session_intervals)
    step_order = 1
    index = 0
    while index < session_intervals_length:
        if (
            planned_session.is_pad_applicable
            and session_intervals[index].time_in_seconds == 0
        ):
            session_intervals[
                index
            ].time_in_seconds = planned_session.pad_time_in_seconds
        is_repeated, sequence_length = check_if_intervals_repeat(
            session_intervals[index:session_intervals_length]
        )
        if is_repeated:
            repeat_steps_list = []
            repeat_step_order = step_order
            step_order += 1
            for repeat_index in range(sequence_length):
                repeat_step_dict = get_single_step_dict(
                    step_order,
                    session_intervals[index + repeat_index],
                    ftp,
                    fthr,
                    data_type,
                )
                repeat_steps_list.append(repeat_step_dict)
                step_order += 1
            repeat_value = 1  # Number of times this sequence will be repeated
            while index + sequence_length < session_intervals_length:
                # Here we will check how many times current sequence is repeated
                sequence_index = 0
                for interval in range(sequence_length):
                    if (
                        session_intervals[index + interval].name
                        != session_intervals[index + interval + sequence_length].name
                    ):
                        break
                    sequence_index = interval
                if sequence_index == (sequence_length - 1):
                    # if sequence_index is equal to (sequence_length - 1), that means
                    # we have a repeated sequence right after the current sequence.
                    # So we will add 1 to repeated value
                    repeat_value += 1

                    # Now we will add the sequence length to the the index, so the
                    # next sequence will become current sequence after that. On the next
                    # loop iteration we will check if there is another repeat sequence
                    # after the new current sequence, and so on.
                    index += sequence_length
                else:
                    break

            # Update the index, as we don't need to iterate over the intervals which are in the repeated steps
            index += sequence_length
            repeat_step = get_repeat_steps_dict(
                repeat_step_order, repeat_value, repeat_steps_list
            )
            steps.append(repeat_step)
            step_order += (
                repeat_value - 1
            ) * sequence_length - 1  # The next step order after the repeating steps
            continue

        # If regular steps i.e. not repeating steps, simply add it to the step dict
        step_dict = get_single_step_dict(
            step_order, session_intervals[index], ftp, fthr, data_type
        )
        steps.append(step_dict)
        step_order += 1
        index += 1

    return steps
