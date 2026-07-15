"""کلاس خودرو"""

import itertools

_id_counter = itertools.count(1)


class Car:
    """
    یک خودرو در صف یکی از مسیرهای چهارراه.

    Attributes:
        id: شناسه یکتای خودرو
        lane_direction: جهتی که خودرو در آن قرار دارد (N, S, E, W)
        arrival_tick: تیک شبیه‌سازی که خودرو وارد صف شده
    """

    __slots__ = ("id", "lane_direction", "arrival_tick")

    def __init__(self, lane_direction: str, arrival_tick: int):
        self.id = next(_id_counter)
        self.lane_direction = lane_direction
        self.arrival_tick = arrival_tick

    def waiting_time(self, current_tick: int) -> int:
        """مدت زمانی که خودرو در صف منتظر مانده است."""
        return current_tick - self.arrival_tick

    def __repr__(self):
        return f"Car(id={self.id}, lane={self.lane_direction})"
