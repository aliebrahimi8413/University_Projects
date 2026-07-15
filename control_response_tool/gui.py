"""رابط گرافیکی: ابزار آموزشی تحلیل پاسخ پله سیستم‌های مرتبه اول و دوم"""

import tkinter as tk
from tkinter import ttk, messagebox

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from transfer_function import TransferFunction
from step_response import StepResponse
from analyzer import Analyzer
from plotter import Plotter


def fmt(value, unit=""):
    if value is None:
        return "—"
    return f"{value:.4g}{unit}"


class ControlAnalysisApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("تحلیل پاسخ سیستم‌های مرتبه اول و دوم")

        self._build_ui()
        self._on_calculate()

    # ---------- رابط ----------

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=10)
        main.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # --- ستون کنترل‌ها ---
        left = ttk.Frame(main)
        left.grid(row=0, column=0, sticky="n", padx=(0, 14))

        ttk.Label(left, text="پارامترهای سیستم", font=("Tahoma", 12, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        ttk.Label(left, text="مرتبه‌ی سیستم:").grid(row=1, column=0, columnspan=2, sticky="w")
        self.order_var = tk.IntVar(value=2)
        ttk.Radiobutton(left, text="مرتبه‌ی اول", variable=self.order_var, value=1,
                        command=self._on_order_change).grid(row=2, column=0, sticky="w")
        ttk.Radiobutton(left, text="مرتبه‌ی دوم", variable=self.order_var, value=2,
                        command=self._on_order_change).grid(row=2, column=1, sticky="w")

        ttk.Label(left, text="K (بهره):").grid(row=3, column=0, sticky="w", pady=(10, 0))
        self.k_var = tk.DoubleVar(value=1.0)
        ttk.Entry(left, textvariable=self.k_var, width=10).grid(row=3, column=1, sticky="w", pady=(10, 0))

        ttk.Label(left, text="ωn (رادیان/ثانیه):").grid(row=4, column=0, sticky="w", pady=(6, 0))
        self.wn_var = tk.DoubleVar(value=1.0)
        ttk.Entry(left, textvariable=self.wn_var, width=10).grid(row=4, column=1, sticky="w", pady=(6, 0))

        self.zeta_label = ttk.Label(left, text="ζ (نسبت میرایی):")
        self.zeta_label.grid(row=5, column=0, sticky="w", pady=(6, 0))
        self.zeta_var = tk.DoubleVar(value=0.5)
        self.zeta_entry = ttk.Entry(left, textvariable=self.zeta_var, width=10)
        self.zeta_entry.grid(row=5, column=1, sticky="w", pady=(6, 0))

        ttk.Button(left, text="محاسبه و رسم", command=self._on_calculate).grid(
            row=6, column=0, columnspan=2, sticky="ew", pady=(14, 4))

        self.stability_label = ttk.Label(left, text="", font=("Tahoma", 9, "bold"))
        self.stability_label.grid(row=7, column=0, columnspan=2, sticky="w", pady=(4, 0))

        ttk.Separator(left, orient="horizontal").grid(
            row=8, column=0, columnspan=2, sticky="ew", pady=10)

        ttk.Label(left, text="شاخص‌های اندازه‌گیری‌شده", font=("Tahoma", 10, "bold")).grid(
            row=9, column=0, columnspan=2, sticky="w")
        self.numeric_text = tk.Text(left, width=32, height=8, font=("Consolas", 9),
                                     bg="#1e1e1e", fg="#e0e0e0", relief="flat")
        self.numeric_text.grid(row=10, column=0, columnspan=2, pady=(4, 0))

        ttk.Label(left, text="فرمول‌های تحلیلی (فقط مرتبه دوم، 0≤ζ<1)",
                 font=("Tahoma", 10, "bold")).grid(row=11, column=0, columnspan=2,
                                                     sticky="w", pady=(10, 0))
        self.analytic_text = tk.Text(left, width=32, height=6, font=("Consolas", 9),
                                      bg="#1e1e1e", fg="#e0e0e0", relief="flat")
        self.analytic_text.grid(row=12, column=0, columnspan=2, pady=(4, 0))

        # --- ستون نمودار ---
        right = ttk.Frame(main)
        right.grid(row=0, column=1, sticky="nsew")
        main.columnconfigure(1, weight=1)

        self.fig, self.ax = plt.subplots(figsize=(7.5, 6))
        self.fig.tight_layout(pad=3)
        self.canvas = FigureCanvasTkAgg(self.fig, master=right)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        self._on_order_change()

    def _on_order_change(self):
        is_second = self.order_var.get() == 2
        state = "normal" if is_second else "disabled"
        self.zeta_entry.config(state=state)

    # ---------- محاسبه و رسم ----------

    def _on_calculate(self):
        try:
            K = self.k_var.get()
            wn = self.wn_var.get()
            order = self.order_var.get()
            zeta = self.zeta_var.get() if order == 2 else None

            tf = TransferFunction(order=order, K=K, omega_n=wn, zeta=zeta)
            sr = StepResponse(tf, num_points=4000)
            t, y = sr.compute()
            an = Analyzer(tf, t, y)
            num = an.numerical_metrics()
            ana = an.analytical_metrics()

            plotter = Plotter(self.ax)
            title = f"پاسخ پله - مرتبه‌ی {order}"
            if order == 2:
                title += f" (ζ={zeta:g}, {tf.damping_category()})"
            plotter.plot(t, y, num, title=title)
            self.canvas.draw()

            self._update_stability_label(tf, num)
            self._update_numeric_panel(num)
            self._update_analytic_panel(ana, order)

        except (ValueError, ZeroDivisionError) as exc:
            messagebox.showerror("خطای ورودی", str(exc))

    def _update_stability_label(self, tf, num):
        if not tf.is_stable():
            self.stability_label.config(
                text="⚠ سیستم پایدار نیست / روی مرز پایداری است", foreground="#e53935")
        else:
            self.stability_label.config(text="✓ سیستم پایدار است", foreground="#43a047")

    def _update_numeric_panel(self, num):
        lines = [
            f"مقدار نهایی    : {fmt(num['final_value'])}",
            f"زمان صعود (Tr) : {fmt(num['rise_time'], ' s')}",
            f"زمان قله (Tp)  : {fmt(num['peak_time'], ' s')}",
            f"فراجهش (Mp)    : {fmt(num['overshoot_percent'], ' %')}",
            f"زمان نشست (Ts) : {fmt(num['settling_time'], ' s')}",
            f"  (معیار نشست: ±{num['settling_tol']*100:.0f}٪)",
        ]
        if num["settling_time"] is None:
            lines.append("  توجه: در بازه‌ی شبیه‌سازی‌شده نشست مشاهده نشد")
        self.numeric_text.delete("1.0", "end")
        self.numeric_text.insert("1.0", "\n".join(lines))

    def _update_analytic_panel(self, ana, order):
        self.analytic_text.delete("1.0", "end")
        if ana is None:
            self.analytic_text.insert("1.0", "برای سیستم مرتبه‌ی اول تعریف نمی‌شود.")
            return
        lines = [
            f"فراجهش (فرمول) : {fmt(ana.get('overshoot_percent'), ' %')}",
            f"زمان قله (فرمول): {fmt(ana.get('peak_time'), ' s')}",
            f"زمان نشست ۲٪   : {fmt(ana.get('settling_time_2pct'), ' s')}",
            f"زمان نشست ۵٪   : {fmt(ana.get('settling_time_5pct'), ' s')}",
        ]
        if "note" in ana:
            lines.append(ana["note"])
        self.analytic_text.insert("1.0", "\n".join(lines))


def main():
    root = tk.Tk()
    app = ControlAnalysisApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
