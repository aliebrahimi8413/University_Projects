"""کلاس کنترل‌کننده چراغ‌های راهنمایی (فاز ثابت / تطبیقی)"""

from intersection import Intersection
from traffic_light import LightState


class Controller:
    """
    کنترل‌کننده‌ی زمان‌بندی چراغ‌های چهارراه.

    دو فاز داریم: NS و EW. هر فاز به ترتیب GREEN -> YELLOW -> (فاز بعدی) RED می‌شود.
    اگر adaptive=True باشد، مدت زمان سبز بر اساس طول صف مسیرهای همان فاز
    و مسیرهای فاز مقابل، به‌صورت پویا محاسبه می‌شود (الگوریتم زمان‌بندی تطبیقی).
    """

    PHASES = ("NS", "EW")

    def __init__(self, intersection: Intersection, adaptive: bool = True,
                 base_green: int = 8, min_green: int = 4, max_green: int = 20,
                 yellow_duration: int = 3):
        self.intersection = intersection
        self.adaptive = adaptive
        self.base_green = base_green
        self.min_green = min_green
        self.max_green = max_green
        self.yellow_duration = yellow_duration

        self.phase_index = 0
        self.sub_state = LightState.GREEN  # GREEN یا YELLOW در فاز جاری
        self._start_phase(self.PHASES[self.phase_index])

    # ---------- منطق اصلی ----------

    def _compute_green_duration(self, phase_name: str) -> int:
        """
        الگوریتم زمان‌بندی تطبیقی.

        نکته‌ی مهم طراحی: به‌جای اینکه هر فاز شلوغ صرفاً سبزش را زیاد کنیم
        (که باعث طولانی‌شدن کل طول چرخه و در نتیجه افزایش انتظار فاز مقابل
        می‌شود)، سبزِ دو فاز را از یک "بودجه‌ی ثابت" زمانی، متناسب با سهم
        صفشان تقسیم می‌کنیم. این باعث می‌شود طول کل چرخه تقریباً ثابت بماند
        و فقط تخصیص داخلی آن بین دو فاز عوض شود (روش مشابه Webster).
        """
        if not self.adaptive:
            return self.base_green

        ns_a, ns_b = self.intersection.pair("NS")
        ew_a, ew_b = self.intersection.pair("EW")
        ns_queue = ns_a.ema_queue + ns_b.ema_queue
        ew_queue = ew_a.ema_queue + ew_b.ema_queue
        total_queue = ns_queue + ew_queue

        budget = 2 * self.base_green  # مجموع سبزِ دو فاز، تقریباً ثابت

        # وقتی صف‌ها خیلی کوچک‌اند، تفاوت آن‌ها بیشتر نویز آماری است تا
        # سیگنال واقعیِ بار ترافیکی؛ در این حالت زمان‌بندی پایه (۵۰/۵۰) را نگه می‌داریم
        # تا زمان‌بند بدون دلیل واقعی نوسان نکند.
        min_queue_to_adapt = 4
        if total_queue < min_queue_to_adapt:
            share = 0.5
        else:
            active_queue = ns_queue if phase_name == "NS" else ew_queue
            share = active_queue / total_queue

        duration = budget * share
        return int(max(self.min_green, min(self.max_green, round(duration))))

    def _start_phase(self, phase_name: str):
        green_duration = self._compute_green_duration(phase_name)
        active_lanes = self.intersection.pair(phase_name)
        other_phase = "EW" if phase_name == "NS" else "NS"
        other_lanes = self.intersection.pair(other_phase)

        for lane in active_lanes:
            lane.light.set_state(LightState.GREEN, green_duration)
        for lane in other_lanes:
            lane.light.set_state(LightState.RED, green_duration + self.yellow_duration)

        self.sub_state = LightState.GREEN
        self.current_phase_name = phase_name

    def _switch_to_yellow(self):
        active_lanes = self.intersection.pair(self.current_phase_name)
        for lane in active_lanes:
            lane.light.set_state(LightState.YELLOW, self.yellow_duration)
        self.sub_state = LightState.YELLOW

    def _advance_phase(self):
        self.phase_index = (self.phase_index + 1) % len(self.PHASES)
        self._start_phase(self.PHASES[self.phase_index])

    def tick(self):
        """
        یک واحد زمانی از شبیه‌سازی را جلو می‌برد:
        ورود خودروهای جدید، خروج خودروها از مسیرهای سبز، و پیشروی زمان‌بند چراغ‌ها.
        """
        self.intersection.spawn_cars()
        self.intersection.discharge_all()
        self.intersection.update_emas()

        for lane in self.intersection.lanes.values():
            lane.light.tick()

        active_lanes = self.intersection.pair(self.current_phase_name)
        # همه چراغ‌های فاز فعال با هم عوض می‌شوند، بررسی یکی کافی است
        if active_lanes[0].light.is_expired():
            if self.sub_state == LightState.GREEN:
                self._switch_to_yellow()
            else:  # YELLOW تمام شده -> فاز بعدی
                self._advance_phase()

        self.intersection.advance_tick()

    def set_adaptive(self, adaptive: bool):
        self.adaptive = adaptive

    def status(self) -> dict:
        return {
            "tick": self.intersection.tick_count,
            "phase": self.current_phase_name,
            "sub_state": self.sub_state.value,
            "adaptive": self.adaptive,
            "lanes": {
                d: {
                    "queue": lane.queue_length(),
                    "state": lane.light.state.value,
                    "remaining": lane.light.remaining,
                    "avg_wait": round(lane.average_wait(), 1),
                }
                for d, lane in self.intersection.lanes.items()
            },
        }
