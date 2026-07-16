# رابط گرافیکی بازی پاندول معکوس
# با tkinter یه گاری و یه میله می‌کشیم و هر چند میلی‌ثانیه صفحه رو آپدیت می‌کنیم

import tkinter as tk
from tkinter import ttk

from simulation import Simulation

# این عدد میگه هر متر از دنیای فیزیکی چند پیکسل روی صفحه بشه
PIXELS_PER_METER = 150

CANVAS_WIDTH = 800
CANVAS_HEIGHT = 400
GROUND_Y = 300  # ارتفاع خط زمین روی صفحه (پیکسل)


class PendulumGame:
    def __init__(self, root):
        self.root = root
        self.root.title("بازی تعادل پاندول معکوس")

        self.sim = Simulation(mode="auto")
        self.running = False

        self._make_widgets()

        # وقتی کاربر کلیدی رو فشار میده یا ول می‌کنه، خبردار بشیم
        self.root.bind("<KeyPress>", self._key_down)
        self.root.bind("<KeyRelease>", self._key_up)

        self.draw()

    def _make_widgets(self):
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(side="top", fill="x")

        self.mode_var = tk.StringVar(value="auto")
        ttk.Radiobutton(top_frame, text="کنترلر خودکار", variable=self.mode_var,
                        value="auto", command=self._change_mode).pack(side="left")
        ttk.Radiobutton(top_frame, text="کنترل دستی (کلید چپ/راست)", variable=self.mode_var,
                        value="manual", command=self._change_mode).pack(side="left", padx=10)

        self.noise_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(top_frame, text="نویز سنسور روشن باشه", variable=self.noise_var,
                        command=self._change_noise).pack(side="left", padx=20)

        self.start_button = ttk.Button(top_frame, text="شروع", command=self._toggle_start)
        self.start_button.pack(side="left", padx=10)

        ttk.Button(top_frame, text="شروع دوباره", command=self._reset).pack(side="left")

        self.canvas = tk.Canvas(self.root, width=CANVAS_WIDTH, height=CANVAS_HEIGHT,
                                 bg="white")
        self.canvas.pack()

        self.info_label = ttk.Label(self.root, text="", font=("Tahoma", 11))
        self.info_label.pack(pady=5)

    def _change_mode(self):
        self.sim.controller.mode = self.mode_var.get()

    def _change_noise(self):
        self.sim.controller.sensor_noise_on = self.noise_var.get()

    def _key_down(self, event):
        self.sim.keys_pressed.add(event.keysym)

    def _key_up(self, event):
        self.sim.keys_pressed.discard(event.keysym)

    def _toggle_start(self):
        self.running = not self.running
        if self.running:
            self.start_button.config(text="توقف")
            self._game_loop()
        else:
            self.start_button.config(text="شروع")

    def _reset(self):
        self.running = False
        self.start_button.config(text="شروع")
        self.sim.reset()
        self._change_mode()
        self._change_noise()
        self.draw()

    def _game_loop(self):
        if not self.running:
            return

        self.sim.step()
        self.draw()

        if self.sim.game_over:
            self.running = False
            self.start_button.config(text="شروع")
            return

        # هر 20 میلی‌ثانیه یه بار این تابع دوباره صدا زده میشه (یعنی حدود ۵۰ فریم در ثانیه)
        self.root.after(20, self._game_loop)

    def draw(self):
        c = self.canvas
        c.delete("all")

        # زمین
        c.create_line(0, GROUND_Y + 25, CANVAS_WIDTH, GROUND_Y + 25, fill="gray")

        # مکان گاری رو از متر به پیکسل تبدیل می‌کنیم (وسط صفحه = صفر متر)
        cart_x_pixels = CANVAS_WIDTH / 2 + self.sim.cart.position * PIXELS_PER_METER
        cart_y = GROUND_Y

        cart_w, cart_h = 80, 40
        c.create_rectangle(cart_x_pixels - cart_w / 2, cart_y - cart_h / 2,
                            cart_x_pixels + cart_w / 2, cart_y + cart_h / 2,
                            fill="#4a90d9", outline="black")

        # میله‌ی پاندول (از وسط گاری شروع میشه و بر اساس زاویه کج میشه)
        pole_len_pixels = self.sim.pendulum.length * 2 * PIXELS_PER_METER
        angle = self.sim.pendulum.angle
        # توجه: زاویه صفر یعنی سیخ رو به بالا. برای رسم از فرمول سینوس‌وکسینوس استفاده می‌کنیم
        import math
        tip_x = cart_x_pixels + pole_len_pixels * math.sin(angle)
        tip_y = (cart_y - cart_h / 2) - pole_len_pixels * math.cos(angle)

        c.create_line(cart_x_pixels, cart_y - cart_h / 2, tip_x, tip_y,
                       fill="#d94a4a", width=6)
        c.create_oval(tip_x - 10, tip_y - 10, tip_x + 10, tip_y + 10,
                      fill="#d94a4a", outline="black")

        if self.sim.game_over:
            c.create_text(CANVAS_WIDTH / 2, 60, text="باختی! دکمه‌ی شروع دوباره رو بزن",
                          fill="red", font=("Tahoma", 18, "bold"))

        self.info_label.config(
            text=f"زمان تعادل: {self.sim.time_survived:.1f} ثانیه   |   "
                 f"زاویه: {self.sim.pendulum.angle_degrees():.1f} درجه"
        )


def main():
    root = tk.Tk()
    game = PendulumGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
