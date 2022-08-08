from decimal import Decimal


def get_initial_max_load(initial_max_load_model):
    max_loads = []

    load = initial_max_load_model.previous_load + Decimal.float(
        initial_max_load_model.ramp_rate
    )
    for _ in range(7):
        max_loads.append(load)
        load = load / initial_max_load_model.lambda_load

    return max_loads.reverse()  # After reversing, its Monday to Sunday now
