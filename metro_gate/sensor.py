# کلاس سنسور - یه نقطه‌ی مشخص روی مسیره که وقتی مسافر از اونجا رد بشه، خبردار میشیم

class Sensor:
    def __init__(self, name, position_x):
        self.name = name
        self.position_x = position_x
        self.triggered = False  # الان یکی جلوشه یا نه

    def check(self, passenger_x):
        # اگه مسافر به اندازه‌ی کافی نزدیک این نقطه شده باشه، سنسور فعال میشه
        self.triggered = passenger_x >= self.position_x
        return self.triggered

    def reset(self):
        self.triggered = False
