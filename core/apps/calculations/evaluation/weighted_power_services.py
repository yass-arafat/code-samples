from decimal import Decimal


class WeightedPowerService:
    """Provides Weighted Power related services"""

    def __init__(self, power_array):
        self.power_array = power_array

    def get_weighted_power(self):
        """Calculates and Returns Weighted Power"""
        if len(self.power_array) < 30:
            weighted_power = 0
            return weighted_power

        average_powers = []

        index = 0
        sum_of_power = 0
        for power in self.power_array:
            index += 1
            sum_of_power += power
            if index < 30:
                continue
            else:
                average_power = sum_of_power / 30
                average_powers.append(average_power)
                sum_of_power -= self.power_array[index - 30]

        sum_of_averages = 0
        for average_power in average_powers:
            sum_of_averages += average_power**4

        mean_power = sum_of_averages / len(average_powers)
        weighted_power = mean_power ** (1 / 4)

        return Decimal(weighted_power)
