# کلاس مسافر - کسی که می‌خواد از گیت رد بشه

class Passenger:
    def __init__(self, name, card, speed=4):
        self.name = name
        self.card = card
        self.speed = speed  # چند پیکسل در هر تیک جلو میره

        self.x = 0.0  # مکان مسافر (از چپ به راست)

        # وضعیت‌های ممکن:
        # "walking"  -> داره میره سمت گیت
        # "waiting"  -> رسیده به گیت و منتظره کارتش چک بشه
        # "passing"  -> کارتش قبول شده و داره رد میشه
        # "blocked"  -> کارتش رد شده (پول کافی نداشت)
        # "done"     -> کامل رد شده و از صحنه خارج شده
        self.state = "walking"

        self.already_tapped = False  # که فقط یه بار کارتش رو چک کنیم
