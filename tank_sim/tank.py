"""
کلاس مخزن آب (Tank)

مدل فیزیکی:
    dV/dt = Qin - Qout
    h = V / A                              (سطح مقطع ثابت مخزن)
    Qout = Cd * A_out * valve_open * sqrt(2*g*h)   (قانون توریچلی، تخلیه‌ی ثقلی)

این یعنی مخزن یک فرآیند غیرخطی است (نه یک انتگرال‌گیر ساده)، چون هرچه سطح آب
بالاتر باشد، فشار و در نتیجه دبی خروجی هم بیشتر می‌شود؛ این خودش یک مکانیزم
تنظیم طبیعی (self-regulating) ایجاد می‌کند و مسئله‌ی کنترل را واقعی‌تر می‌کند.
"""

import math

G = 9.81  # شتاب گرانش، m/s^2


class Tank:
    def __init__(self, capacity_liters: float = 300.0, area_m2: float = 0.5,
                 outlet_area_m2: float = 0.00008, discharge_coeff: float = 0.6,
                 initial_level_m: float = 0.0):
        """
        Args:
            capacity_liters: ظرفیت مخزن بر حسب لیتر (طبق پروژه: 300)
            area_m2: مساحت سطح مقطع افقی مخزن (m^2)
            outlet_area_m2: مساحت سوراخ خروجی مخزن (m^2)
            discharge_coeff: ضریب تخلیه (Cd) قانون توریچلی، معمولاً 0.6-0.65
            initial_level_m: ارتفاع اولیه‌ی آب (m)
        """
        self.capacity_m3 = capacity_liters / 1000.0
        self.area = area_m2
        self.outlet_area = outlet_area_m2
        self.cd = discharge_coeff
        self.max_height = self.capacity_m3 / self.area

        self.height = max(0.0, min(initial_level_m, self.max_height))
        self.volume = self.height * self.area

        self.valve_open = 1.0  # درصد بازبودن شیر خروجی/مصرف (0 تا 1) - دیسترابنس

    def outflow_rate(self) -> float:
        """دبی خروجی فعلی بر اساس قانون توریچلی (m^3/s)."""
        if self.height <= 0:
            return 0.0
        return self.cd * self.outlet_area * self.valve_open * math.sqrt(2 * G * self.height)

    def step(self, qin_m3s: float, dt: float):
        """
        یک گام زمانی شبیه‌سازی: تراز حجمی مخزن را با ورودی/خروجی به‌روزرسانی می‌کند.

        Args:
            qin_m3s: دبی ورودی از پمپ (m^3/s)
            dt: گام زمانی (ثانیه)
        """
        qout = self.outflow_rate()
        dv = (qin_m3s - qout) * dt
        self.volume = max(0.0, min(self.volume + dv, self.capacity_m3))
        self.height = self.volume / self.area

    def level_percent(self) -> float:
        return 100.0 * self.volume / self.capacity_m3

    def __repr__(self):
        return f"Tank(height={self.height:.3f}m, level={self.level_percent():.1f}%)"
