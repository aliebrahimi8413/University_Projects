# کلاس Simulation - اینجا فیزیک واقعی حرکت پاندول و گاری حساب میشه
# فرمول‌هاش از فیزیک "پاندول معکوس روی گاری" هست که یه مسئله‌ی معروف در درس کنترله

import math

from cart import Cart
from pendulum import Pendulum
from controller import Controller

GRAVITY = 9.8
DT = 0.02  # هر گام شبیه‌سازی چقدر زمان جلو میره (ثانیه)

# اگه زاویه از این مقدار بیشتر بشه، دیگه نمیشه جمعش کرد -> باخت
FALL_ANGLE_DEG = 30


class Simulation:
    def __init__(self, mode="auto"):
        self.cart = Cart()
        self.pendulum = Pendulum()
        self.controller = Controller(mode=mode)

        self.time_survived = 0.0
        self.game_over = False
        self.keys_pressed = set()

    def reset(self):
        self.cart = Cart()
        self.pendulum = Pendulum()
        self.time_survived = 0.0
        self.game_over = False
        self.keys_pressed = set()  # مهمه که پاک بشه، وگرنه اگه کاربر موقع باخت
                                    # کلیدی رو نگه داشته باشه، بعد از ریست هم
                                    # انگار همون کلید هنوز فشرده‌ست

    def step(self):
        if self.game_over:
            return

        force = self.controller.get_force(self.pendulum, self.cart, self.keys_pressed)
        self._physics_step(force)

        self.time_survived += DT

        # چک می‌کنیم آیا باخته یا نه
        if abs(self.pendulum.angle) > math.radians(FALL_ANGLE_DEG):
            self.game_over = True
        if abs(self.cart.position) > self.cart.track_limit:
            self.game_over = True

    def _physics_step(self, force):
        # این فرمول‌ها معادلات حرکت پاندول-روی-گاری هستن (از منابع کلاسیک کنترل)
        m = self.pendulum.mass
        M = self.cart.mass
        l = self.pendulum.length
        theta = self.pendulum.angle
        theta_dot = self.pendulum.angle_speed

        total_mass = M + m
        pole_mass_length = m * l

        cos_t = math.cos(theta)
        sin_t = math.sin(theta)

        temp = (force + pole_mass_length * theta_dot ** 2 * sin_t) / total_mass
        theta_acc = (GRAVITY * sin_t - cos_t * temp) / (
            l * (4.0 / 3.0 - m * cos_t ** 2 / total_mass)
        )
        x_acc = temp - pole_mass_length * theta_acc * cos_t / total_mass

        # روش اویلر ساده برای جلو بردن زمان (ساده‌ترین روش انتگرال‌گیری عددی)
        self.cart.speed += x_acc * DT
        self.cart.position += self.cart.speed * DT
        self.pendulum.angle_speed += theta_acc * DT
        self.pendulum.angle += self.pendulum.angle_speed * DT
