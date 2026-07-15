"""کلاس Simulation: اجرای حلقه‌ی شبیه‌سازی و ثبت تاریخچه"""

from tank import Tank
from pump import Pump
from sensor import Sensor
from controller import Controller


class Simulation:
    def __init__(self, tank: Tank, pump: Pump, sensor: Sensor,
                 controller: Controller, dt: float = 0.5):
        self.tank = tank
        self.pump = pump
        self.sensor = sensor
        self.controller = controller
        self.dt = dt
        self.time = 0.0

        self.history = {
            "t": [], "height": [], "measured": [], "command": [],
            "qin_lpm": [], "qout_lpm": [], "setpoint": [], "valve_open": [],
        }

    def step(self):
        measured = self.sensor.read(self.tank.height, self.dt)
        command = self.controller.compute(measured, self.dt)
        self.pump.set_command(command)
        qin = self.pump.step(self.dt)
        self.tank.step(qin, self.dt)

        self.time += self.dt
        self._log(measured, command, qin)

    def _log(self, measured, command, qin):
        h = self.history
        h["t"].append(self.time)
        h["height"].append(self.tank.height)
        h["measured"].append(measured)
        h["command"].append(command)
        h["qin_lpm"].append(qin * 60000)
        h["qout_lpm"].append(self.tank.outflow_rate() * 60000)
        h["setpoint"].append(self.controller.setpoint)
        h["valve_open"].append(self.tank.valve_open)

    def run(self, duration_s: float, disturbance_fn=None):
        """
        شبیه‌سازی را به مدت duration_s ثانیه اجرا می‌کند.

        Args:
            disturbance_fn: تابع اختیاری f(t) -> valve_open (0..1) برای اعمال
                             تغییرات دیسترابنس (مثلاً مصرف بیشتر آب) در طول زمان
        """
        steps = int(duration_s / self.dt)
        for _ in range(steps):
            if disturbance_fn is not None:
                self.tank.valve_open = disturbance_fn(self.time)
            self.step()
        return self.history
