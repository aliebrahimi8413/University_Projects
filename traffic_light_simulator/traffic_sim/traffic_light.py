"""کلاس چراغ راهنمایی"""

from enum import Enum


class LightState(Enum):
    RED = "RED"
    YELLOW = "YELLOW"
    GREEN = "GREEN"


class TrafficLight:
    """
    یک چراغ راهنمایی که وضعیت و زمان باقی‌مانده تا تغییر وضعیت را نگه می‌دارد.
    """

    def __init__(self, name: str):
        self.name = name
        self.state = LightState.RED
        self.remaining = 0  # ثانیه/تیک باقی‌مانده در وضعیت فعلی

    def set_state(self, state: LightState, duration: int):
        self.state = state
        self.remaining = duration

    def tick(self):
        """یک واحد زمانی سپری می‌شود."""
        if self.remaining > 0:
            self.remaining -= 1

    def is_expired(self) -> bool:
        return self.remaining <= 0

    def is_green(self) -> bool:
        return self.state == LightState.GREEN

    def __repr__(self):
        return f"TrafficLight({self.name}, {self.state.value}, {self.remaining}s)"
