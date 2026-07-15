"""
مقایسه‌ی کنترل On-Off و PID روی یک سناریوی یکسان (شامل یک دیسترابنس ناگهانی
در مصرف آب) و رسم نمودار سطح آب برای هر دو.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from tank import Tank
from pump import Pump
from sensor import Sensor
from controller import OnOffController, PIDController
from simulation import Simulation

SETPOINT = 0.4  # متر
DURATION = 1200  # ثانیه


def disturbance(t):
    """تا t=600 مصرف عادی (شیر کمی باز)، بعد از آن مصرف بیشتر (شیر بازتر)."""
    return 1.0 if t < 600 else 1.8


def run(ctrl):
    tank = Tank(capacity_liters=300, area_m2=0.5, initial_level_m=0.1)
    pump = Pump(max_flow_lpm=20, tau=1.5)
    sensor = Sensor(noise_std_m=0.001, response_tau=0.3)
    sim = Simulation(tank, pump, sensor, ctrl, dt=0.5)
    sim.run(duration_s=DURATION, disturbance_fn=disturbance)
    return sim.history


def summarize(name, h):
    import statistics
    steady = h["height"][-200:]  # 100 ثانیه‌ی آخر
    mean_err = abs(SETPOINT - statistics.mean(steady))
    std_dev = statistics.pstdev(steady)
    overshoot = max(0.0, max(h["height"]) - SETPOINT)
    print(f"{name:6s} | میانگین خطای پایدار={mean_err*1000:.1f}mm  "
          f"نوسان پایدار(std)={std_dev*1000:.2f}mm  overshoot اوج={overshoot*1000:.1f}mm")


def main():
    onoff_hist = run(OnOffController(setpoint_m=SETPOINT, hysteresis_m=0.02))
    pid_hist = run(PIDController(setpoint_m=SETPOINT, kp=40, ki=5, kd=2))

    print("--- مقایسه‌ی کمی ---")
    summarize("OnOff", onoff_hist)
    summarize("PID", pid_hist)

    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    ax1 = axes[0]
    ax1.plot(onoff_hist["t"], [x * 100 for x in onoff_hist["height"]],
              label="On-Off", color="#e53935", linewidth=1.2)
    ax1.plot(pid_hist["t"], [x * 100 for x in pid_hist["height"]],
              label="PID", color="#1e88e5", linewidth=1.2)
    ax1.axhline(SETPOINT * 100, color="#43a047", linestyle="--",
                label="Setpoint")
    ax1.axvline(600, color="gray", linestyle=":", label="تغییر دیسترابنس (t=600s)")
    ax1.set_ylabel("سطح آب (cm)")
    ax1.set_title("مقایسه‌ی کنترل On-Off و PID روی سطح مخزن")
    ax1.legend(loc="lower right")
    ax1.grid(alpha=0.3)

    ax2 = axes[1]
    ax2.plot(onoff_hist["t"], onoff_hist["command"], label="On-Off command",
              color="#e53935", linewidth=0.8)
    ax2.plot(pid_hist["t"], pid_hist["command"], label="PID command",
              color="#1e88e5", linewidth=0.8)
    ax2.set_ylabel("فرمان پمپ (0 تا 1)")
    ax2.set_xlabel("زمان (ثانیه)")
    ax2.legend(loc="upper right")
    ax2.grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig("/mnt/user-data/outputs/tank_controller_comparison.png", dpi=140)
    print("نمودار ذخیره شد.")


if __name__ == "__main__":
    main()
