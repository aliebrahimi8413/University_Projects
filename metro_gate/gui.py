# رابط گرافیکی گیت مترو - با tkinter یه گیت و مسافرا رو می‌کشیم

import tkinter as tk
from tkinter import ttk

from gate import Gate
from passenger import Passenger
from card import Card

SCENE_WIDTH = 600
SCENE_HEIGHT = 200
GATE_X = 300  # وسط صحنه، جایی که درب‌ها هستن
GATE_HALF_WIDTH = 40

passenger_counter = 1  # برای اسم‌گذاری مسافرای جدید


class MetroGateGame:
    def __init__(self, root):
        self.root = root
        self.root.title("شبیه‌ساز گیت مترو")

        self.gate = Gate(scene_width=SCENE_WIDTH,
                          entry_x=GATE_X - GATE_HALF_WIDTH,
                          exit_x=GATE_X + GATE_HALF_WIDTH,
                          fare=10000)
        self.running = False

        self._make_widgets()
        self.draw()

    def _make_widgets(self):
        top = ttk.Frame(self.root, padding=10)
        top.pack(side="top", fill="x")

        ttk.Button(top, text="مسافر با کارت شارژدار",
                  command=self._add_normal_passenger).pack(side="left", padx=4)
        ttk.Button(top, text="مسافر با کارت خالی",
                  command=self._add_empty_card_passenger).pack(side="left", padx=4)

        self.start_button = ttk.Button(top, text="شروع", command=self._toggle_run)
        self.start_button.pack(side="left", padx=20)

        self.canvas = tk.Canvas(self.root, width=SCENE_WIDTH, height=SCENE_HEIGHT, bg="#eeeeee")
        self.canvas.pack(padx=10, pady=10)

        bottom = ttk.Frame(self.root, padding=10)
        bottom.pack(side="top", fill="x")
        ttk.Label(bottom, text="رویدادها:", font=("Tahoma", 10, "bold")).pack(anchor="w")
        self.log_label = ttk.Label(bottom, text="", font=("Consolas", 9), justify="left")
        self.log_label.pack(anchor="w")

    def _add_normal_passenger(self):
        global passenger_counter
        name = f"مسافر {passenger_counter}"
        passenger_counter += 1
        card = Card(card_id=name, balance=50000)
        self.gate.add_passenger(Passenger(name, card))
        self._refresh_log()

    def _add_empty_card_passenger(self):
        global passenger_counter
        name = f"مسافر {passenger_counter}"
        passenger_counter += 1
        card = Card(card_id=name, balance=2000)  # کمتر از کرایه
        self.gate.add_passenger(Passenger(name, card))
        self._refresh_log()

    def _toggle_run(self):
        self.running = not self.running
        self.start_button.config(text="توقف" if self.running else "شروع")
        if self.running:
            self._loop()

    def _loop(self):
        if not self.running:
            return
        self.gate.update()
        self.draw()
        self._refresh_log()
        self.root.after(30, self._loop)

    def _refresh_log(self):
        self.log_label.config(text="\n".join(self.gate.log))

    def draw(self):
        c = self.canvas
        c.delete("all")

        mid_y = SCENE_HEIGHT // 2

        # خط زمین (مسیر راه رفتن مسافرا)
        c.create_line(0, mid_y + 30, SCENE_WIDTH, mid_y + 30, fill="gray")

        # چهارچوب گیت (دیوارای دو طرف)
        c.create_rectangle(GATE_X - GATE_HALF_WIDTH - 10, mid_y - 60,
                            GATE_X - GATE_HALF_WIDTH, mid_y + 30, fill="#888")
        c.create_rectangle(GATE_X + GATE_HALF_WIDTH, mid_y - 60,
                            GATE_X + GATE_HALF_WIDTH + 10, mid_y + 30, fill="#888")

        # درب‌ها - بر اساس door_position از وسط به‌سمت بیرون باز میشن
        door_pos = self.gate.motor.door_position
        door_open_amount = door_pos * GATE_HALF_WIDTH

        # درب چپ
        c.create_rectangle(GATE_X - GATE_HALF_WIDTH - door_open_amount, mid_y - 55,
                            GATE_X - door_open_amount, mid_y - 45,
                            fill="#e53935", outline="black")
        # درب راست
        c.create_rectangle(GATE_X + door_open_amount, mid_y - 55,
                            GATE_X + GATE_HALF_WIDTH + door_open_amount, mid_y - 45,
                            fill="#e53935", outline="black")

        # سنسورها (فقط برای نمایش، دایره‌ی کوچیک)
        c.create_oval(self.gate.entry_sensor.position_x - 4, mid_y - 65,
                      self.gate.entry_sensor.position_x + 4, mid_y - 57,
                      fill=("yellow" if self.gate.entry_sensor.triggered else "gray"))
        c.create_oval(self.gate.exit_sensor.position_x - 4, mid_y - 65,
                      self.gate.exit_sensor.position_x + 4, mid_y - 57,
                      fill=("yellow" if self.gate.exit_sensor.triggered else "gray"))

        # مسافر فعال رو رسم کن
        p = self.gate.active
        if p is not None and p.state != "done":
            color = "#4a90d9"
            if p.state == "blocked":
                color = "#e53935"

            c.create_oval(p.x - 10, mid_y + 5, p.x + 10, mid_y + 25, fill=color)
            c.create_text(p.x, mid_y - 10, text=f"{p.name}\n{p.card.balance} ت",
                         font=("Tahoma", 8))

            if p.state == "blocked":
                c.create_text(p.x, mid_y + 40, text="رد شد!", fill="red",
                             font=("Tahoma", 10, "bold"))

        # تعداد نفرات تو صف
        c.create_text(SCENE_WIDTH - 60, 20, text=f"صف: {len(self.gate.queue)} نفر",
                      font=("Tahoma", 9))


def main():
    root = tk.Tk()
    game = MetroGateGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
