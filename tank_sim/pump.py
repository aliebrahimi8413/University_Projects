"""کلاس پمپ (Pump)"""


class Pump:
    """
    پمپ ورودی مخزن. فرمان کنترلی (0 تا 1) را به دبی واقعی تبدیل می‌کند.

    برای واقعی‌تر شدن مدل، پمپ به‌صورت آنی به فرمان جدید نمی‌رسد؛ یک تأخیر
    مرتبه‌ی اول (فیلتر) دارد که با ثابت زمانی tau مشخص می‌شود:
        d(Qactual)/dt = (command * Qmax - Qactual) / tau
    """

    def __init__(self, max_flow_lpm: float = 20.0, tau: float = 1.5):
        """
        Args:
            max_flow_lpm: حداکثر دبی پمپ بر حسب لیتر بر دقیقه
            tau: ثابت زمانی پاسخ پمپ (ثانیه) - هرچه بزرگ‌تر، پمپ کندتر
        """
        self.max_flow_m3s = (max_flow_lpm / 1000.0) / 60.0
        self.tau = tau
        self.command = 0.0       # فرمان کنترلر: 0 تا 1
        self.actual_flow = 0.0   # دبی واقعی خروجی پمپ (m^3/s)

    def set_command(self, command: float):
        self.command = max(0.0, min(1.0, command))

    def step(self, dt: float) -> float:
        """دبی واقعی پمپ را طبق دینامیک تأخیری به‌روزرسانی و برمی‌گرداند."""
        target = self.command * self.max_flow_m3s
        if self.tau <= 0:
            self.actual_flow = target
        else:
            self.actual_flow += (target - self.actual_flow) * (dt / self.tau)
        return self.actual_flow

    def __repr__(self):
        return f"Pump(command={self.command:.2f}, flow={self.actual_flow*60000:.2f} L/min)"
