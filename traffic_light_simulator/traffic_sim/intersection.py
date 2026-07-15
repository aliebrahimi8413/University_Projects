"""کلاس چهارراه (Intersection)"""

from lane import Lane

DIRECTIONS = ("N", "S", "E", "W")


class Intersection:
    """
    چهارراهی با چهار مسیر ورودی: شمال، جنوب، شرق، غرب.
    خودروهای N/S یک جفت هستند و همزمان چراغشان سبز/قرمز می‌شود؛
    همینطور E/W جفت دیگر هستند (چهارراه معمولی با دو فاز).
    """

    def __init__(self, arrival_rates: dict[str, float] | None = None):
        arrival_rates = arrival_rates or {}
        self.lanes: dict[str, Lane] = {
            d: Lane(d, arrival_rate=arrival_rates.get(d, 0.25))
            for d in DIRECTIONS
        }
        self.tick_count = 0

    def pair(self, name: str) -> tuple[Lane, Lane]:
        """برمی‌گرداند دو مسیر متعلق به یک فاز: 'NS' یا 'EW'."""
        if name == "NS":
            return self.lanes["N"], self.lanes["S"]
        elif name == "EW":
            return self.lanes["E"], self.lanes["W"]
        raise ValueError("phase name must be 'NS' or 'EW'")

    def spawn_cars(self):
        """در تمام مسیرها به‌صورت تصادفی خودروی جدید تولید می‌کند."""
        for lane in self.lanes.values():
            lane.maybe_spawn_car(self.tick_count)

    def discharge_all(self):
        """در مسیرهایی که چراغشان سبز است خودرو خارج می‌کند."""
        for lane in self.lanes.values():
            lane.discharge(self.tick_count)

    def update_emas(self):
        for lane in self.lanes.values():
            lane.update_ema()

    def advance_tick(self):
        self.tick_count += 1

    def total_queue_length(self) -> int:
        return sum(lane.queue_length() for lane in self.lanes.values())

    def __repr__(self):
        return f"Intersection(tick={self.tick_count}, lanes={list(self.lanes.values())})"
