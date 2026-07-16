# کلاس گیت - مغز اصلی برنامه. سنسورها و موتور رو کنترل می‌کنه و تصمیم
# می‌گیره کارت مسافر رو قبول کنه یا رد کنه

from motor import Motor
from sensor import Sensor


class Gate:
    def __init__(self, scene_width=600, entry_x=250, exit_x=350, fare=10000):
        self.scene_width = scene_width
        self.fare = fare

        self.motor = Motor()
        self.entry_sensor = Sensor("سنسور ورودی", entry_x)
        self.exit_sensor = Sensor("سنسور خروجی", exit_x)

        self.queue = []      # مسافرایی که تو صف منتظرن
        self.active = None   # مسافری که الان داره رد میشه

        self.close_timer = 0  # چند تیک صبر کنیم بعد رد شدن مسافر تا درب ببنده

        self.log = []  # پیام‌های اتفاقاتی که افتاده (برای نمایش تو GUI)

    def add_passenger(self, passenger):
        self.queue.append(passenger)
        self._log(f"{passenger.name} وارد صف شد")

    def _log(self, message):
        self.log.append(message)
        if len(self.log) > 6:
            self.log.pop(0)

    def update(self):
        # هر تیک اول موتور رو آپدیت می‌کنیم (کم‌کم باز/بسته بشه)
        self.motor.update()

        # اگه الان کسی فعال نیست و صف خالی نیست، نفر بعدی رو بیار جلو
        if self.active is None and self.queue:
            self.active = self.queue.pop(0)

        if self.active is not None:
            self._update_active_passenger()

        # اگه وقتشه درب رو ببندیم
        if self.close_timer > 0:
            self.close_timer -= 1
            if self.close_timer == 0:
                self.motor.close_door()

    def _update_active_passenger(self):
        p = self.active

        if p.state == "walking":
            p.x += p.speed
            # رسید به سنسور ورودی؟ (فقط یه بار کارتش رو چک می‌کنیم)
            if not p.already_tapped and self.entry_sensor.check(p.x):
                p.already_tapped = True
                self._check_card(p)

        elif p.state == "waiting":
            # منتظر باز شدن درب
            if self.motor.is_open_enough():
                p.state = "passing"

        elif p.state == "passing":
            still_inside_gate = p.x < self.exit_sensor.position_x
            if still_inside_gate:
                # هنوز داخل محدوده‌ی درب‌هاست؛ فقط وقتی درب باز باشه حرکت کنه
                if self.motor.is_open_enough():
                    p.x += p.speed
            else:
                # از درب رد شده؛ دیگه فرقی نمی‌کنه درب چه حالتیه، آزادانه راه میره
                p.x += p.speed

            if self.exit_sensor.check(p.x) and self.close_timer == 0:
                self.close_timer = 30  # چند تیک دیگه صبر کن، بعد درب رو ببند

            if p.x > self.scene_width:
                p.state = "done"
                self._log(f"{p.name} با موفقیت رد شد")
                self._clear_active()

        elif p.state == "blocked":
            # کارتش رد شده، باید برگرده عقب
            p.x -= p.speed
            if p.x <= 0:
                p.state = "done"
                self._clear_active()

    def _check_card(self, p):
        if p.card.has_enough_money(self.fare):
            p.card.pay(self.fare)
            self.motor.open_door()
            p.state = "waiting"
            self._log(f"کارت {p.name} قبول شد (موجودی جدید: {p.card.balance})")
        else:
            p.state = "blocked"
            self._log(f"کارت {p.name} رد شد - موجودی کافی نیست")

    def _clear_active(self):
        self.active = None
        self.entry_sensor.reset()
        self.exit_sensor.reset()
