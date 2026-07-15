"""
کلاس TransferFunction

ساخت تابع تبدیل حلقه‌باز G(s) برای دو نوع سیستم آموزشی رایج در کنترل:

    مرتبه‌ی اول:   G(s) = K / (s/omega_n + 1) = K*omega_n / (s + omega_n)
                   (omega_n در اینجا معادل 1/tau است: هرچه بزرگ‌تر، سیستم سریع‌تر)

    مرتبه‌ی دوم:   G(s) = K*omega_n^2 / (s^2 + 2*zeta*omega_n*s + omega_n^2)

از پارامتر omega_n برای هر دو مرتبه استفاده می‌شود تا واسط کاربری ساده و
یکنواخت بماند: omega_n "سرعت" سیستم را نشان می‌دهد و zeta فقط برای
مرتبه‌ی دوم معنا دارد (میزان میرایی نوسان).
"""

from scipy import signal


class TransferFunction:
    def __init__(self, order: int, K: float, omega_n: float, zeta: float = None):
        if order not in (1, 2):
            raise ValueError("order باید 1 یا 2 باشد")
        if omega_n <= 0:
            raise ValueError("omega_n باید مثبت باشد")
        if order == 2 and (zeta is None or zeta < 0):
            raise ValueError("برای سیستم مرتبه‌ی دوم مقدار zeta (>= 0) لازم است")

        self.order = order
        self.K = K
        self.omega_n = omega_n
        self.zeta = zeta if order == 2 else None

        if order == 1:
            num = [K * omega_n]
            den = [1, omega_n]
        else:
            num = [K * omega_n ** 2]
            den = [1, 2 * zeta * omega_n, omega_n ** 2]

        self.num = num
        self.den = den
        self.system = signal.TransferFunction(num, den)

    def dc_gain(self) -> float:
        """بهره‌ی حالت پایدار (مقدار نهایی پاسخ پله برای سیستم پایدار)."""
        return self.K

    def poles(self):
        return self.system.poles

    def is_stable(self) -> bool:
        return all(p.real < 0 for p in self.poles())

    def damping_category(self) -> str:
        """فقط برای مرتبه‌ی دوم: دسته‌بندی نوع میرایی."""
        if self.order != 2:
            return "n/a"
        z = self.zeta
        if z == 0:
            return "بدون میرایی (نوسانی دائمی)"
        if z < 1:
            return "کمتر از حد میرایی (underdamped)"
        if z == 1:
            return "میرایی بحرانی (critically damped)"
        return "بیش‌میرا (overdamped)"

    def __repr__(self):
        return f"TransferFunction(order={self.order}, num={self.num}, den={self.den})"
