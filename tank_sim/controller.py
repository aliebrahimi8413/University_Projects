"""کلاس‌های کنترل‌کننده: On-Off و PID ساده"""

from abc import ABC, abstractmethod


class Controller(ABC):
    """کلاس پایه‌ی انتزاعی برای کنترل‌کننده‌های سطح مخزن."""

    def __init__(self, setpoint_m: float):
        self.setpoint = setpoint_m

    @abstractmethod
    def compute(self, measurement_m: float, dt: float) -> float:
        """فرمان کنترلی (0 تا 1) را برای پمپ محاسبه می‌کند."""
        raise NotImplementedError

    def reset(self):
        pass


class OnOffController(Controller):
    """
    کنترل روشن/خاموش با هیسترزیس (باند مرگ) برای جلوگیری از سوییچینگ خیلی سریع.

    اگر سطح آب کمتر از setpoint - hysteresis/2 باشد -> پمپ روشن (1.0)
    اگر سطح آب بیشتر از setpoint + hysteresis/2 باشد -> پمپ خاموش (0.0)
    در غیر این صورت وضعیت قبلی حفظ می‌شود (رفتار هیسترزیس).
    """

    def __init__(self, setpoint_m: float, hysteresis_m: float = 0.02):
        super().__init__(setpoint_m)
        self.hysteresis = hysteresis_m
        self._pump_on = True

    def compute(self, measurement_m: float, dt: float) -> float:
        low = self.setpoint - self.hysteresis / 2
        high = self.setpoint + self.hysteresis / 2
        if measurement_m < low:
            self._pump_on = True
        elif measurement_m > high:
            self._pump_on = False
        return 1.0 if self._pump_on else 0.0

    def reset(self):
        self._pump_on = True


class PIDController(Controller):
    """
    کنترل‌کننده‌ی PID با:
      - مشتق‌گیری روی اندازه‌گیری (derivative-on-measurement) برای جلوگیری
        از "ضربه‌ی مشتقی" (derivative kick) هنگام تغییر ناگهانی setpoint
      - Anti-windup با محدودسازی (clamping) جمله‌ی انتگرالی
      - محدودسازی خروجی نهایی در بازه‌ی [0, 1]
    """

    def __init__(self, setpoint_m: float, kp: float = 40.0, ki: float = 5.0,
                 kd: float = 2.0, output_limits=(0.0, 1.0)):
        super().__init__(setpoint_m)
        self.kp, self.ki, self.kd = kp, ki, kd
        self.out_min, self.out_max = output_limits
        self._integral = 0.0
        self._prev_measurement = None

    def compute(self, measurement_m: float, dt: float) -> float:
        error = self.setpoint - measurement_m

        if self._prev_measurement is None:
            derivative = 0.0
        else:
            derivative = -(measurement_m - self._prev_measurement) / dt
        self._prev_measurement = measurement_m

        # جمله تناسبی و مشتقی
        p_term = self.kp * error
        d_term = self.kd * derivative

        # جمله انتگرالی با anti-windup: فقط اگر خروجی اشباع نشده انتگرال بگیر
        tentative_integral = self._integral + error * dt
        tentative_output = p_term + self.ki * tentative_integral + d_term

        if self.out_min <= tentative_output <= self.out_max:
            self._integral = tentative_integral

        output = p_term + self.ki * self._integral + d_term
        return max(self.out_min, min(self.out_max, output))

    def reset(self):
        self._integral = 0.0
        self._prev_measurement = None
