"""کلاس سنسور سطح آب (Sensor)"""

import random


class Sensor:
    """
    سنسور اندازه‌گیری ارتفاع آب. برای واقعی‌تر شدن، نویز اندازه‌گیری و
    یک فیلتر پایین‌گذر ساده (شبیه‌سازی زمان پاسخ سنسور) دارد.
    """

    def __init__(self, noise_std_m: float = 0.001, response_tau: float = 0.3):
        """
        Args:
            noise_std_m: انحراف معیار نویز گاوسی روی اندازه‌گیری (m)
            response_tau: ثابت زمانی فیلتر پاسخ سنسور (ثانیه)؛ 0 یعنی آنی
        """
        self.noise_std = noise_std_m
        self.tau = response_tau
        self.filtered_value = 0.0
        self._initialized = False

    def read(self, true_height: float, dt: float) -> float:
        noisy = true_height + random.gauss(0.0, self.noise_std)
        if not self._initialized:
            self.filtered_value = noisy
            self._initialized = True
        elif self.tau <= 0:
            self.filtered_value = noisy
        else:
            self.filtered_value += (noisy - self.filtered_value) * (dt / self.tau)
        return max(0.0, self.filtered_value)
