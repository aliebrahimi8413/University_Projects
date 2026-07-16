# کلاس پاندول (میله‌ای که باید بایسه و نیفته)

import math


class Pendulum:
    def __init__(self):
        # زاویه رو بر حسب رادیان نگه می‌داریم. زاویه صفر یعنی کاملا سیخ وایساده
        self.angle = math.radians(3)   # یه کم کج شروع میشه که بازی جالب باشه
        self.angle_speed = 0.0         # سرعت زاویه‌ای (چقدر سریع داره کج میشه)

        self.mass = 0.1   # جرم پاندول (کیلوگرم)
        self.length = 0.5  # طول پاندول از وسط تا نوک (متر)

    def angle_degrees(self):
        # فقط برای نمایش راحت‌تر روی صفحه، تبدیل به درجه
        return math.degrees(self.angle)
