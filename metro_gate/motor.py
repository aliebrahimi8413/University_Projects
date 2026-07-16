# کلاس موتور - درب‌های گیت رو باز و بسته می‌کنه (نه یهویی، بلکه کم‌کم)

class Motor:
    def __init__(self, speed=0.05):
        # door_position بین 0 (کاملا بسته) تا 1 (کاملا باز) در نوسانه
        self.door_position = 0.0
        self.speed = speed  # هر تیک چقدر درب حرکت کنه

        # وضعیت‌های موتور: "closed", "opening", "open", "closing"
        self.state = "closed"

    def open_door(self):
        if self.state != "open":
            self.state = "opening"

    def close_door(self):
        if self.state != "closed":
            self.state = "closing"

    def update(self):
        # این تابع هر تیک صدا زده میشه و کم‌کم درب رو حرکت میده
        if self.state == "opening":
            self.door_position += self.speed
            if self.door_position >= 1.0:
                self.door_position = 1.0
                self.state = "open"

        elif self.state == "closing":
            self.door_position -= self.speed
            if self.door_position <= 0.0:
                self.door_position = 0.0
                self.state = "closed"

    def is_open_enough(self):
        # مسافر وقتی میتونه رد بشه که درب حداقل ۷۰٪ باز باشه
        return self.door_position >= 0.7
