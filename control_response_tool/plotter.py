"""کلاس Plotter: رسم نمودار پاسخ پله با حاشیه‌نویسی شاخص‌های عملکردی"""

import numpy as np


class Plotter:
    """
    رسم پاسخ پله روی یک Axes از matplotlib، همراه با خط‌های راهنمای:
    مقدار نهایی، ±۲٪ باند نشست، نقطه‌ی قله (در صورت وجود فراجهش)، و
    بازه‌ی زمان صعود (۱۰٪ تا ۹۰٪).
    """

    def __init__(self, ax):
        self.ax = ax

    def plot(self, t, y, metrics: dict, title: str = "پاسخ پله"):
        ax = self.ax
        ax.clear()

        ax.plot(t, y, color="#1e88e5", linewidth=1.6, label="پاسخ پله")

        fv = metrics["final_value"]
        ax.axhline(fv, color="#43a047", linestyle="--", linewidth=1,
                   label=f"مقدار نهایی = {fv:g}")

        tol = metrics.get("settling_tol", 0.02)
        band = tol * abs(fv)
        ax.axhspan(fv - band, fv + band, color="#43a047", alpha=0.12,
                  label=f"باند ±{tol*100:.0f}٪")

        if metrics.get("peak_time") is not None:
            tp, yp = metrics["peak_time"], metrics["peak_value"]
            ax.plot([tp], [yp], "o", color="#e53935", markersize=6)
            ax.annotate(f"قله\nt={tp:.3g}s", xy=(tp, yp),
                       xytext=(tp, yp + 0.08 * max(abs(fv), 1e-9)),
                       ha="center", fontsize=8, color="#e53935")

        if metrics.get("settling_time") is not None:
            ts = metrics["settling_time"]
            ax.axvline(ts, color="#8e24aa", linestyle=":", linewidth=1.2,
                      label=f"زمان نشست ≈ {ts:.3g}s")

        ax.set_xlabel("زمان (s)")
        ax.set_ylabel("خروجی")
        ax.set_title(title)
        ax.legend(loc="lower right", fontsize=8)
        ax.grid(alpha=0.3)
        return ax
