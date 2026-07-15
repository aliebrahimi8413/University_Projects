"""
کلاس Analyzer: استخراج شاخص‌های استاندارد پاسخ پله

دو دسته شاخص محاسبه می‌شود:

1) numerical_metrics: مستقیماً از داده‌ی شبیه‌سازی‌شده اندازه‌گیری می‌شود.
   این روش برای هر نوع سیستم (مرتبه ۱ یا ۲، هر مقدار zeta) درست کار می‌کند
   و منبع اصلی و قابل‌اعتماد اعداد در این ابزار است.

2) analytical_metrics: فرمول‌های بسته‌ی کلاسیک کنترل، فقط برای سیستم مرتبه‌ی
   دوم کمترمیرا (0 <= zeta < 1) معتبرند. توجه: برای «زمان صعود» فرمول بسته‌ی
   دقیقی که همه‌جا پذیرفته‌شده باشد وجود ندارد (کتاب‌های مختلف تقریب‌های
   متفاوتی می‌دهند)، بنابراین این ابزار برای rise time فقط مقدار اندازه‌گیری‌
   شده را گزارش می‌کند تا عدد نادرستی به‌عنوان «فرمول دقیق» جا زده نشود.
"""

import math
import numpy as np

from transfer_function import TransferFunction


class Analyzer:
    def __init__(self, tf: TransferFunction, t: np.ndarray, y: np.ndarray):
        self.tf = tf
        self.t = t
        self.y = y
        self.final_value = tf.dc_gain()

    # ---------- شاخص‌های اندازه‌گیری‌شده (عددی، همیشه معتبر) ----------

    def rise_time(self, low=0.1, high=0.9):
        """زمان صعود بین low و high نسبت به مقدار نهایی (پیش‌فرض ۱۰٪ تا ۹۰٪)."""
        fv = self.final_value
        if fv == 0:
            return None
        target_low = low * fv
        target_high = high * fv
        t_low = self._first_crossing(target_low)
        t_high = self._first_crossing(target_high)
        if t_low is None or t_high is None:
            return None
        return t_high - t_low

    def _first_crossing(self, target):
        y, t = self.y, self.t
        for i in range(1, len(y)):
            if (y[i - 1] < target <= y[i]) or (y[i - 1] > target >= y[i]):
                # درون‌یابی خطی بین دو نمونه برای دقت بیشتر
                frac = (target - y[i - 1]) / (y[i] - y[i - 1])
                return t[i - 1] + frac * (t[i] - t[i - 1])
        return None

    def peak(self):
        idx = int(np.argmax(self.y))
        return self.t[idx], self.y[idx]

    def has_genuine_overshoot(self) -> bool:
        """آیا پاسخ واقعاً از مقدار نهایی گذشته (فراجهش دارد) یا صرفاً یکنواخت صعودی است."""
        _, peak_val = self.peak()
        fv = self.final_value
        return peak_val > fv * 1.001  # کمی تلورانس برای خطای عددی

    def overshoot_percent(self):
        fv = self.final_value
        if fv == 0:
            return 0.0
        _, peak_val = self.peak()
        return max(0.0, (peak_val - fv) / fv * 100.0)

    def settling_time(self, tol=0.02):
        """
        اولین زمانی که پاسخ برای همیشه (تا انتهای بازه‌ی شبیه‌سازی‌شده) در
        باند ± tol×مقدار نهایی می‌ماند. اگر تا پایان بازه هم خارج از باند
        باشد، None برمی‌گرداند (یعنی نشست در افق شبیه‌سازی مشاهده نشد).
        """
        fv = self.final_value
        if fv == 0:
            return None
        band = tol * abs(fv)
        within = np.abs(self.y - fv) <= band
        if within.all():
            return self.t[0]
        violations = np.where(~within)[0]
        last_violation = violations[-1]
        if last_violation + 1 >= len(self.t):
            return None  # هرگز درون بازه‌ی شبیه‌سازی‌شده نشست نکرد
        return self.t[last_violation + 1]

    def numerical_metrics(self, settling_tol=0.02):
        tp, peak_val = self.peak()
        genuine = self.has_genuine_overshoot()
        return {
            "final_value": self.final_value,
            "rise_time": self.rise_time(),
            "peak_time": tp if genuine else None,
            "peak_value": peak_val if genuine else None,
            "overshoot_percent": self.overshoot_percent(),
            "settling_time": self.settling_time(tol=settling_tol),
            "settling_tol": settling_tol,
        }

    # ---------- شاخص‌های تحلیلی (فرمول بسته، فقط مرتبه‌ی دوم کمترمیرا) ----------

    def analytical_metrics(self):
        if self.tf.order != 2:
            return None
        zeta, wn = self.tf.zeta, self.tf.omega_n
        result = {"valid_range": "0 <= zeta < 1"}
        if 0 <= zeta < 1:
            wd = wn * math.sqrt(1 - zeta ** 2)
            result["overshoot_percent"] = math.exp(-zeta * math.pi / math.sqrt(1 - zeta ** 2)) * 100
            result["peak_time"] = math.pi / wd
            result["settling_time_2pct"] = 4.6 / (zeta * wn) if zeta > 0 else None
            result["settling_time_5pct"] = 3.0 / (zeta * wn) if zeta > 0 else None
        else:
            result["overshoot_percent"] = 0.0
            result["peak_time"] = None
            result["settling_time_2pct"] = None
            result["settling_time_5pct"] = None
            result["note"] = "zeta >= 1: بدون فراجهش، فرمول‌های بسته برای Ts/Tp اینجا اعمال نمی‌شوند"
        return result
