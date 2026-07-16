# کلاس کنترلر - این کلاسه که تصمیم میگیره چقدر نیرو به گاری وارد بشه
# دو حالت داره: دستی (با کیبورد) و خودکار (کامپیوتر خودش تعادل رو نگه میداره)

import math
import random


class Controller:
    def __init__(self, mode="auto"):
        self.mode = mode  # "manual" یا "auto"

        # این عددا رو با آزمون‌وخطا پیدا کردم (چندتا مقدار رو تست کردم تا
        # دیدم پاندول رو نمی‌ندازه). به این جور کنترل میگن state feedback
        self.k_angle = 50.0
        self.k_angle_speed = 10.0
        self.k_position = 1.0
        self.k_speed = 1.0

        self.max_force = 20.0

        # برای بخش نمره‌ی اضافه: نویز سنسور
        self.sensor_noise_on = False
        self.sensor_noise_std_deg = 2.0  # هرچی بیشتر، سنسور بی‌دقت‌تر

    def read_angle_with_noise(self, real_angle):
        # به‌جای زاویه‌ی واقعی، یه زاویه‌ی کمی اشتباه به کنترلر میدیم
        # (شبیه‌سازی یه سنسور واقعی که همیشه یه ذره خطا داره)
        if not self.sensor_noise_on:
            return real_angle
        noise = math.radians(random.gauss(0, self.sensor_noise_std_deg))
        return real_angle + noise

    def get_force(self, pendulum, cart, keys_pressed):
        if self.mode == "manual":
            return self._manual_force(keys_pressed)
        else:
            return self._auto_force(pendulum, cart)

    def _manual_force(self, keys_pressed):
        # کاربر با کلید چپ و راست، گاری رو هل میده
        force = 0.0
        if "Left" in keys_pressed:
            force -= 15.0
        if "Right" in keys_pressed:
            force += 15.0
        return force

    def _auto_force(self, pendulum, cart):
        angle_seen = self.read_angle_with_noise(pendulum.angle)

        # فرمول ساده‌ی فیدبک: هرچی پاندول بیشتر کج بشه یا سریع‌تر کج بشه،
        # یا گاری از وسط دور بشه، نیروی بیشتری برای اصلاحش میزنیم
        force = (self.k_angle * angle_seen
                 + self.k_angle_speed * pendulum.angle_speed
                 + self.k_position * cart.position
                 + self.k_speed * cart.speed)

        # نیرو رو محدود می‌کنیم که موتور فرضی بی‌نهایت قوی نباشه
        if force > self.max_force:
            force = self.max_force
        if force < -self.max_force:
            force = -self.max_force

        return force
