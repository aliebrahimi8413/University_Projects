"""کلاس مسیر (Lane) هر ضلع چهارراه"""

import random
from collections import deque
from car import Car
from traffic_light import TrafficLight


class Lane:
    """
    یک مسیر ورودی به چهارراه (مثلاً شمال، جنوب، شرق، غرب).
    شامل صف خودروها، نرخ ورود خودرو و چراغ راهنمایی مربوط به خودش.
    """

    def __init__(self, direction: str, arrival_rate: float = 0.25,
                 discharge_rate: int = 1, max_queue_display: int = 20):
        """
        Args:
            direction: نام جهت مسیر (N/S/E/W)
            arrival_rate: احتمال ورود یک خودروی جدید در هر تیک (0 تا 1)
            discharge_rate: تعداد خودرویی که در هر تیک سبز از صف خارج می‌شود
        """
        self.direction = direction
        self.arrival_rate = arrival_rate
        self.discharge_rate = discharge_rate
        self.queue: deque[Car] = deque()
        self.light = TrafficLight(direction)
        self.total_departed = 0
        self.total_wait_ticks = 0
        self.max_queue_display = max_queue_display

        # میانگین متحرک نمایی طول صف؛ برای کنترل‌کننده‌ی تطبیقی به‌کار می‌رود
        # تا نوسانات لحظه‌ای/نویز آماری صف باعث تصمیم‌گیری نادرست نشود.
        self.ema_queue = 0.0
        self._ema_alpha = 0.15

    def update_ema(self):
        self.ema_queue = (self._ema_alpha * len(self.queue)
                           + (1 - self._ema_alpha) * self.ema_queue)

    def maybe_spawn_car(self, current_tick: int):
        """با احتمال arrival_rate یک خودروی جدید به صف اضافه می‌کند."""
        if random.random() < self.arrival_rate:
            self.queue.append(Car(self.direction, current_tick))

    def queue_length(self) -> int:
        return len(self.queue)

    def discharge(self, current_tick: int) -> int:
        """
        اگر چراغ سبز باشد، به تعداد discharge_rate خودرو از صف خارج می‌شود.
        تعداد خودروهای واقعاً خارج‌شده را برمی‌گرداند.
        """
        if not self.light.is_green():
            return 0
        departed = 0
        for _ in range(self.discharge_rate):
            if not self.queue:
                break
            car = self.queue.popleft()
            self.total_wait_ticks += car.waiting_time(current_tick)
            self.total_departed += 1
            departed += 1
        return departed

    def average_wait(self) -> float:
        if self.total_departed == 0:
            return 0.0
        return self.total_wait_ticks / self.total_departed

    def __repr__(self):
        return f"Lane({self.direction}, queue={len(self.queue)}, {self.light.state.value})"
