"""نمایش گرافیکی شبیه‌سازی چهارراه با tkinter"""

import tkinter as tk
from tkinter import ttk

from intersection import Intersection
from controller import Controller

CANVAS_SIZE = 640
CENTER = CANVAS_SIZE // 2
ROAD_HALF_WIDTH = 60
LIGHT_COLORS = {"RED": "#e53935", "YELLOW": "#fdd835", "GREEN": "#43a047"}

# موقعیت هر جهت روی بوم: (x, y) پایه برای رسم صف و چراغ
DIR_INFO = {
    "N": {"axis": "v", "sign": -1},
    "S": {"axis": "v", "sign": 1},
    "E": {"axis": "h", "sign": 1},
    "W": {"axis": "h", "sign": -1},
}


class TrafficSimApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("شبیه‌ساز چراغ راهنمایی هوشمند")

        self.intersection = Intersection(
            arrival_rates={"N": 0.28, "S": 0.28, "E": 0.14, "W": 0.14}
        )
        self.controller = Controller(self.intersection, adaptive=True)

        self.running = False
        self.speed_ms = 400  # هر تیک شبیه‌سازی هر چند میلی‌ثانیه اجرا شود

        self._build_ui()
        self._draw_static_road()
        self.redraw()

    # ---------- ساخت رابط ----------

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=10)
        main.grid(row=0, column=0, sticky="nsew")

        self.canvas = tk.Canvas(main, width=CANVAS_SIZE, height=CANVAS_SIZE,
                                 bg="#2b2b2b", highlightthickness=0)
        self.canvas.grid(row=0, column=0, rowspan=8, padx=(0, 12))

        side = ttk.Frame(main)
        side.grid(row=0, column=1, sticky="n")

        ttk.Label(side, text="کنترل شبیه‌سازی", font=("Tahoma", 12, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(0, 8), sticky="w")

        self.start_btn = ttk.Button(side, text="شروع", command=self.toggle_running)
        self.start_btn.grid(row=1, column=0, sticky="ew", pady=2)

        reset_btn = ttk.Button(side, text="ریست", command=self.reset)
        reset_btn.grid(row=1, column=1, sticky="ew", pady=2, padx=(4, 0))

        self.adaptive_var = tk.BooleanVar(value=True)
        adaptive_chk = ttk.Checkbutton(
            side, text="زمان‌بندی تطبیقی", variable=self.adaptive_var,
            command=self._on_adaptive_toggle)
        adaptive_chk.grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 2))

        ttk.Label(side, text="سرعت شبیه‌سازی:").grid(row=3, column=0, columnspan=2,
                                                        sticky="w", pady=(8, 0))
        self.speed_scale = ttk.Scale(side, from_=50, to=1000, value=self.speed_ms,
                                      command=self._on_speed_change)
        self.speed_scale.grid(row=4, column=0, columnspan=2, sticky="ew")

        ttk.Separator(side, orient="horizontal").grid(
            row=5, column=0, columnspan=2, sticky="ew", pady=10)

        ttk.Label(side, text="وضعیت مسیرها", font=("Tahoma", 11, "bold")).grid(
            row=6, column=0, columnspan=2, sticky="w")

        self.status_text = tk.Text(side, width=34, height=14, bg="#1e1e1e",
                                    fg="#e0e0e0", font=("Consolas", 10),
                                    relief="flat")
        self.status_text.grid(row=7, column=0, columnspan=2, pady=(6, 0))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

    def _on_adaptive_toggle(self):
        self.controller.set_adaptive(self.adaptive_var.get())

    def _on_speed_change(self, value):
        self.speed_ms = int(float(value))

    # ---------- رسم ثابت جاده ----------

    def _draw_static_road(self):
        c = self.canvas
        # جاده افقی و عمودی
        c.create_rectangle(0, CENTER - ROAD_HALF_WIDTH, CANVAS_SIZE,
                            CENTER + ROAD_HALF_WIDTH, fill="#444444", outline="")
        c.create_rectangle(CENTER - ROAD_HALF_WIDTH, 0, CENTER + ROAD_HALF_WIDTH,
                            CANVAS_SIZE, fill="#444444", outline="")
        # خط‌چین وسط جاده‌ها
        for x in range(0, CANVAS_SIZE, 30):
            if CENTER - ROAD_HALF_WIDTH - 15 < x < CENTER + ROAD_HALF_WIDTH + 15:
                continue
            c.create_line(x, CENTER, x + 15, CENTER, fill="#bdbdbd", dash=(4, 4))
        for y in range(0, CANVAS_SIZE, 30):
            if CENTER - ROAD_HALF_WIDTH - 15 < y < CENTER + ROAD_HALF_WIDTH + 15:
                continue
            c.create_line(CENTER, y, CENTER, y + 15, fill="#bdbdbd", dash=(4, 4))

        labels = {"N": (CENTER, 15), "S": (CENTER, CANVAS_SIZE - 15),
                  "E": (CANVAS_SIZE - 15, CENTER), "W": (15, CENTER)}
        for d, (x, y) in labels.items():
            c.create_text(x, y, text=d, fill="white", font=("Tahoma", 14, "bold"))

    # ---------- رسم پویا ----------

    def redraw(self):
        c = self.canvas
        c.delete("dynamic")

        for direction, lane in self.intersection.lanes.items():
            self._draw_lane_light(lane, direction)
            self._draw_lane_queue(lane, direction)

        self._update_status_panel()

    def _light_position(self, direction):
        offset = ROAD_HALF_WIDTH + 24
        if direction == "N":
            return CENTER - 20, CENTER - offset
        if direction == "S":
            return CENTER + 20, CENTER + offset
        if direction == "E":
            return CENTER + offset, CENTER - 20
        if direction == "W":
            return CENTER - offset, CENTER + 20

    def _draw_lane_light(self, lane, direction):
        x, y = self._light_position(direction)
        color = LIGHT_COLORS[lane.light.state.value]
        r = 12
        self.canvas.create_oval(x - r, y - r, x + r, y + r, fill=color,
                                 outline="#111111", width=2, tags="dynamic")
        self.canvas.create_text(x, y + r + 12, text=str(lane.light.remaining),
                                 fill="white", font=("Consolas", 9), tags="dynamic")

    def _draw_lane_queue(self, lane, direction):
        """خودروهای منتظر را به‌صورت مستطیل‌های کوچک در امتداد مسیر رسم می‌کند."""
        info = DIR_INFO[direction]
        car_gap = 16
        car_w, car_h = 22, 12
        count = min(lane.queue_length(), 18)  # محدود برای خوانایی بصری

        for i in range(count):
            dist = ROAD_HALF_WIDTH + 30 + i * car_gap
            if info["axis"] == "v":
                cx = CENTER + (20 if info["sign"] < 0 else -20)
                cy = CENTER + info["sign"] * dist
                self.canvas.create_rectangle(cx - car_h, cy - car_w // 2,
                                              cx + car_h, cy + car_w // 2,
                                              fill="#64b5f6", outline="#0d47a1",
                                              tags="dynamic")
            else:
                cx = CENTER + info["sign"] * dist
                cy = CENTER + (20 if info["sign"] < 0 else -20)
                self.canvas.create_rectangle(cx - car_w // 2, cy - car_h,
                                              cx + car_w // 2, cy + car_h,
                                              fill="#64b5f6", outline="#0d47a1",
                                              tags="dynamic")

        if lane.queue_length() > count:
            x, y = self._light_position(direction)
            self.canvas.create_text(
                x, y - 26, text=f"+{lane.queue_length() - count}",
                fill="#ffeb3b", font=("Tahoma", 9, "bold"), tags="dynamic")

    def _update_status_panel(self):
        s = self.controller.status()
        lines = [
            f"تیک شبیه‌سازی: {s['tick']}",
            f"فاز فعال: {s['phase']} ({s['sub_state']})",
            f"حالت: {'تطبیقی' if s['adaptive'] else 'ثابت'}",
            "",
        ]
        for d in ("N", "S", "E", "W"):
            info = s["lanes"][d]
            lines.append(
                f"{d}: صف={info['queue']:<3} {info['state']:<7} "
                f"مانده={info['remaining']:<3} میانگین‌انتظار={info['avg_wait']}"
            )
        self.status_text.delete("1.0", "end")
        self.status_text.insert("1.0", "\n".join(lines))

    # ---------- حلقه شبیه‌سازی ----------

    def toggle_running(self):
        self.running = not self.running
        self.start_btn.config(text="توقف" if self.running else "شروع")
        if self.running:
            self._loop()

    def _loop(self):
        if not self.running:
            return
        self.controller.tick()
        self.redraw()
        self.root.after(self.speed_ms, self._loop)

    def reset(self):
        self.running = False
        self.start_btn.config(text="شروع")
        self.intersection = Intersection(
            arrival_rates={"N": 0.28, "S": 0.28, "E": 0.14, "W": 0.14}
        )
        self.controller = Controller(self.intersection,
                                      adaptive=self.adaptive_var.get())
        self.redraw()


def main():
    root = tk.Tk()
    app = TrafficSimApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
