"""رابط گرافیکی شبیه‌سازی مخزن آب: نمایش مخزن + نمودار زنده‌ی سطح + انتخاب کنترلر"""

import tkinter as tk
from tkinter import ttk

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from tank import Tank
from pump import Pump
from sensor import Sensor
from controller import OnOffController, PIDController
from simulation import Simulation

DT = 0.5
HISTORY_WINDOW_S = 300  # چند ثانیه‌ی اخیر روی نمودار نمایش داده شود


class TankSimApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("شبیه‌ساز مخزن آب و کنترل سطح")

        self.setpoint = 0.4
        self.valve_open = 1.0
        self.running = False

        self._build_models()
        self._build_ui()
        self.redraw()

    # ---------- ساخت مدل‌ها ----------

    def _build_models(self):
        self.tank = Tank(capacity_liters=300, area_m2=0.5, initial_level_m=0.05)
        self.pump = Pump(max_flow_lpm=20, tau=1.5)
        self.sensor = Sensor(noise_std_m=0.001, response_tau=0.3)
        self.controller = OnOffController(setpoint_m=self.setpoint, hysteresis_m=0.02)
        self.sim = Simulation(self.tank, self.pump, self.sensor, self.controller, dt=DT)
        self.tank.valve_open = self.valve_open

    # ---------- ساخت رابط ----------

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=10)
        main.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # --- بخش چپ: نمایش مخزن ---
        left = ttk.Frame(main)
        left.grid(row=0, column=0, sticky="n", padx=(0, 12))

        self.tank_canvas = tk.Canvas(left, width=160, height=360, bg="#f0f0f0",
                                      highlightthickness=1, highlightbackground="#999")
        self.tank_canvas.grid(row=0, column=0)

        self.info_label = ttk.Label(left, text="", font=("Consolas", 10),
                                     justify="left")
        self.info_label.grid(row=1, column=0, pady=(10, 0), sticky="w")

        # --- بخش وسط: نمودار زنده ---
        mid = ttk.Frame(main)
        mid.grid(row=0, column=1, sticky="nsew")
        main.columnconfigure(1, weight=1)

        self.fig, (self.ax_level, self.ax_cmd) = plt.subplots(
            2, 1, figsize=(7, 5.5), sharex=True, gridspec_kw={"height_ratios": [2, 1]})
        self.fig.tight_layout(pad=2.5)
        self.canvas_plot = FigureCanvasTkAgg(self.fig, master=mid)
        self.canvas_plot.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        # --- بخش راست: کنترل‌ها ---
        right = ttk.Frame(main)
        right.grid(row=0, column=2, sticky="n", padx=(12, 0))

        ttk.Label(right, text="کنترل شبیه‌سازی", font=("Tahoma", 12, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        self.start_btn = ttk.Button(right, text="شروع", command=self.toggle_running)
        self.start_btn.grid(row=1, column=0, sticky="ew", pady=2)
        ttk.Button(right, text="ریست", command=self.reset).grid(
            row=1, column=1, sticky="ew", pady=2, padx=(4, 0))

        ttk.Label(right, text="نوع کنترلر:").grid(row=2, column=0, columnspan=2,
                                                     sticky="w", pady=(10, 0))
        self.controller_var = tk.StringVar(value="OnOff")
        ttk.Radiobutton(right, text="On-Off", variable=self.controller_var,
                         value="OnOff", command=self._on_controller_change).grid(
            row=3, column=0, sticky="w")
        ttk.Radiobutton(right, text="PID", variable=self.controller_var,
                         value="PID", command=self._on_controller_change).grid(
            row=3, column=1, sticky="w")

        ttk.Label(right, text="نقطه‌ی تنظیم (setpoint):").grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(10, 0))
        self.setpoint_var = tk.DoubleVar(value=self.setpoint * 100)
        setpoint_scale = ttk.Scale(right, from_=10, to=55, variable=self.setpoint_var,
                                    command=self._on_setpoint_change)
        setpoint_scale.grid(row=5, column=0, columnspan=2, sticky="ew")

        ttk.Label(right, text="دیسترابنس (بازبودن شیر مصرف):").grid(
            row=6, column=0, columnspan=2, sticky="w", pady=(10, 0))
        self.valve_var = tk.DoubleVar(value=self.valve_open)
        valve_scale = ttk.Scale(right, from_=0.2, to=2.5, variable=self.valve_var,
                                 command=self._on_valve_change)
        valve_scale.grid(row=7, column=0, columnspan=2, sticky="ew")

        ttk.Separator(right, orient="horizontal").grid(
            row=8, column=0, columnspan=2, sticky="ew", pady=10)
        ttk.Label(right, text="ضرایب PID:", font=("Tahoma", 10, "bold")).grid(
            row=9, column=0, columnspan=2, sticky="w")

        self.kp_var = tk.DoubleVar(value=40.0)
        self.ki_var = tk.DoubleVar(value=5.0)
        self.kd_var = tk.DoubleVar(value=2.0)
        for i, (label, var) in enumerate([("Kp", self.kp_var), ("Ki", self.ki_var),
                                           ("Kd", self.kd_var)]):
            ttk.Label(right, text=label).grid(row=10 + i, column=0, sticky="w")
            entry = ttk.Entry(right, textvariable=var, width=8)
            entry.grid(row=10 + i, column=1, sticky="w")
            entry.bind("<Return>", lambda e: self._on_controller_change())

        right.columnconfigure(0, weight=1)
        right.columnconfigure(1, weight=1)

    # ---------- رویدادها ----------

    def _on_controller_change(self):
        self.setpoint = self.setpoint_var.get() / 100.0
        if self.controller_var.get() == "OnOff":
            self.controller = OnOffController(setpoint_m=self.setpoint, hysteresis_m=0.02)
        else:
            self.controller = PIDController(
                setpoint_m=self.setpoint, kp=self.kp_var.get(),
                ki=self.ki_var.get(), kd=self.kd_var.get())
        self.sim.controller = self.controller

    def _on_setpoint_change(self, value):
        self.setpoint = float(value) / 100.0
        self.controller.setpoint = self.setpoint

    def _on_valve_change(self, value):
        self.valve_open = float(value)
        self.tank.valve_open = self.valve_open

    def toggle_running(self):
        self.running = not self.running
        self.start_btn.config(text="توقف" if self.running else "شروع")
        if self.running:
            self._loop()

    def reset(self):
        self.running = False
        self.start_btn.config(text="شروع")
        self._build_models()
        self._on_controller_change()
        self.tank.valve_open = self.valve_open
        self.redraw()

    def _loop(self):
        if not self.running:
            return
        self.sim.step()
        self.redraw()
        self.root.after(int(DT * 200), self._loop)  # سرعت نمایش چندبرابر واقعی

    # ---------- رسم ----------

    def redraw(self):
        self._draw_tank()
        self._draw_chart()
        self._update_info()

    def _draw_tank(self):
        c = self.tank_canvas
        c.delete("all")
        W, H = 160, 360
        margin = 20
        tank_top, tank_bottom = margin, H - margin
        tank_left, tank_right = 30, W - 30

        c.create_rectangle(tank_left, tank_top, tank_right, tank_bottom,
                            outline="#333", width=2)

        frac = self.tank.height / self.tank.max_height
        water_top = tank_bottom - frac * (tank_bottom - tank_top)
        c.create_rectangle(tank_left, water_top, tank_right, tank_bottom,
                            fill="#42a5f5", outline="")

        sp_frac = self.controller.setpoint / self.tank.max_height
        sp_y = tank_bottom - sp_frac * (tank_bottom - tank_top)
        c.create_line(tank_left - 8, sp_y, tank_right + 8, sp_y,
                      fill="#e53935", dash=(4, 2), width=2)
        c.create_text(tank_right + 8, sp_y - 8, text="SP", fill="#e53935",
                      anchor="w", font=("Tahoma", 8, "bold"))

        pump_color = "#43a047" if self.pump.command > 0.05 else "#9e9e9e"
        c.create_rectangle(tank_left - 22, tank_bottom - 20, tank_left - 6,
                            tank_bottom, fill=pump_color, outline="#333")
        c.create_text(tank_left - 14, tank_bottom + 10, text="پمپ",
                      font=("Tahoma", 8))

    def _draw_chart(self):
        h = self.sim.history
        t = h["t"]
        if not t:
            return
        window_start = max(0, t[-1] - HISTORY_WINDOW_S)
        idx0 = 0
        for i, tv in enumerate(t):
            if tv >= window_start:
                idx0 = i
                break

        self.ax_level.clear()
        self.ax_level.plot(t[idx0:], [x * 100 for x in h["height"][idx0:]],
                            color="#1e88e5", linewidth=1.3, label="سطح آب")
        self.ax_level.axhline(self.controller.setpoint * 100, color="#e53935",
                               linestyle="--", linewidth=1, label="Setpoint")
        self.ax_level.set_ylabel("سطح (cm)")
        self.ax_level.set_ylim(0, self.tank.max_height * 100 + 5)
        self.ax_level.legend(loc="upper left", fontsize=8)
        self.ax_level.grid(alpha=0.3)

        self.ax_cmd.clear()
        self.ax_cmd.plot(t[idx0:], h["command"][idx0:], color="#43a047",
                          linewidth=1.0)
        self.ax_cmd.set_ylabel("فرمان پمپ")
        self.ax_cmd.set_xlabel("زمان (s)")
        self.ax_cmd.set_ylim(-0.05, 1.05)
        self.ax_cmd.grid(alpha=0.3)

        self.canvas_plot.draw()

    def _update_info(self):
        lines = [
            f"زمان: {self.sim.time:.1f} s",
            f"سطح واقعی: {self.tank.height*100:.1f} cm",
            f"سطح اندازه‌گیری‌شده: {self.sensor.filtered_value*100:.1f} cm",
            f"فرمان پمپ: {self.pump.command:.2f}",
            f"دبی ورودی: {self.pump.actual_flow*60000:.2f} L/min",
            f"دبی خروجی: {self.tank.outflow_rate()*60000:.2f} L/min",
        ]
        self.info_label.config(text="\n".join(lines))


def main():
    root = tk.Tk()
    app = TankSimApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
