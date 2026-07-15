"""کلاس StepResponse: محاسبه‌ی پاسخ پله‌ی سیستم با افق زمانی مناسب و خودکار"""

import math
import numpy as np
from scipy import signal

from transfer_function import TransferFunction


class StepResponse:
    def __init__(self, tf: TransferFunction, num_points: int = 2000):
        self.tf = tf
        self.num_points = num_points
        self.t = None
        self.y = None
        self.duration = None
        self.fully_settled_in_horizon = True

    def _auto_duration(self) -> float:
        """
        افق زمانی شبیه‌سازی را بر اساس قطب واقعیِ سیستم انتخاب می‌کند (نه فقط
        تقریب zeta*omega_n)، چون آن تقریب برای سیستم‌های بیش‌میرا (overdamped)
        دست‌کم‌گویی می‌کند: در آن حالت قطب کندتر، کندتر از zeta*wn افت می‌کند
        و اگر افق را کوتاه انتخاب کنیم پاسخ هنوز به ۹۰٪ مقدار نهایی نرسیده و
        محاسبه‌ی rise/settling time شکست می‌خورد.
        """
        wn = self.tf.omega_n
        poles = self.tf.poles()
        real_parts = [abs(p.real) for p in poles]
        imag_parts = [abs(p.imag) for p in poles]

        damped_reals = [r for r in real_parts if r > 1e-9]
        if not damped_reals:
            # بدون میرایی: هرگز نمی‌نشیند؛ چند دوره‌ی کامل نوسان نشان می‌دهیم
            osc_freqs = [w for w in imag_parts if w > 1e-9]
            period = 2 * math.pi / min(osc_freqs) if osc_freqs else 2 * math.pi / wn
            return 6 * period

        slowest_decay_rate = min(damped_reals)  # کندترین قطب، تعیین‌کننده‌ی مدت نشست
        tau_slow = 1.0 / slowest_decay_rate
        duration = 7.0 * tau_slow
        # برای سیستم‌های سریع (قطب غالب بزرگ)، حداقل زمان کافی برای دیدن صعود اولیه هم لازم است
        return max(duration, 5.0 / wn)

    def compute(self):
        self.duration = self._auto_duration()
        t = np.linspace(0, self.duration, self.num_points)
        t_out, y_out = signal.step(self.tf.system, T=t)
        self.t = t_out
        self.y = y_out
        return self.t, self.y
