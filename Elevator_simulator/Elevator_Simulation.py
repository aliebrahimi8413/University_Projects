import itertools
import tkinter as tk
from tkinter import ttk, messagebox
import random

A = 6
NUM_FLOORS = 10 * A  # 60 floors, numbered 0..59 (0 = lobby)


FLOOR_HEIGHT = 22          # ارتفاع هر طبقه روی کانواس (پیکسل)
SHAFT_X0, SHAFT_X1 = 260, 320   # موقعیت افقی چاه آسانسور
CANVAS_WIDTH = 520
TICK_MS = 120               # هر تیک شبیه‌سازی هر چند میلی‌ثانیه انجام شود

class Person:
    """یک مسافر که در یک طبقه منتظر آسانسور است و مقصد مشخصی دارد."""

    _id_counter = itertools.count(1)

    def __init__(self, origin_floor: int, destination_floor: int, request_time: float):
        if origin_floor == destination_floor:
            raise ValueError("مبدأ و مقصد نمی‌توانند یکسان باشند")
        self.id = next(Person._id_counter)
        self.origin_floor = origin_floor
        self.destination_floor = destination_floor
        self.request_time = request_time      # زمانی که درخواست داده شده
        self.pickup_time = None                # زمانی که سوار آسانسور شده
        self.dropoff_time = None               # زمانی که پیاده شده

    @property
    def direction(self) -> int:
        """جهت درخواستی: +1 بالا، -1 پایین"""
        return 1 if self.destination_floor > self.origin_floor else -1

    @property
    def wait_time(self):
        """زمان انتظار تا سوار شدن (اگر هنوز سوار نشده، None)"""
        if self.pickup_time is None:
            return None
        return self.pickup_time - self.request_time

    @property
    def travel_time(self):
        if self.dropoff_time is None or self.pickup_time is None:
            return None
        return self.dropoff_time - self.pickup_time

    def __repr__(self):
        return f"Person#{self.id}({self.origin_floor}->{self.destination_floor})"


class Floor:
    """یک طبقه از ساختمان؛ صف افراد منتظر به تفکیک جهت درخواست."""

    def __init__(self, number: int):
        self.number = number
        self.waiting_up: list[Person] = []
        self.waiting_down: list[Person] = []

    def add_request(self, person: Person):
        if person.direction == 1:
            self.waiting_up.append(person)
        else:
            self.waiting_down.append(person)

    def has_request(self, direction: int) -> bool:
        return bool(self.waiting_up) if direction == 1 else bool(self.waiting_down)

    def pop_boarding(self, direction: int, capacity_left: int):
        """افرادی که در این جهت منتظرند و می‌توانند سوار شوند را برمی‌گرداند و از صف حذف می‌کند."""
        queue = self.waiting_up if direction == 1 else self.waiting_down
        boarding = queue[:capacity_left]
        del queue[:capacity_left]
        return boarding

    def __repr__(self):
        return f"Floor({self.number}, up={len(self.waiting_up)}, down={len(self.waiting_down)})"


class Elevator:
    """آسانسور: موقعیت، جهت حرکت، ظرفیت و مسافران داخل آن."""

    IDLE, MOVING_UP, MOVING_DOWN = "IDLE", "UP", "DOWN"

    def __init__(self, capacity: int = 8):
        self.current_floor = 0
        self.capacity = capacity
        self.passengers: list[Person] = []
        self.state = Elevator.IDLE
        self.target_floors: set[int] = set()  # طبقاتی که باید توقف کند (مقصد مسافران داخل)

    @property
    def load(self):
        return len(self.passengers)

    @property
    def free_capacity(self):
        return self.capacity - self.load

    def board(self, people: list, now: float):
        for p in people:
            p.pickup_time = now
            self.passengers.append(p)
            self.target_floors.add(p.destination_floor)

    def unload_at(self, floor: int, now: float):
        leaving = [p for p in self.passengers if p.destination_floor == floor]
        for p in leaving:
            p.dropoff_time = now
            self.passengers.remove(p)
        self.target_floors.discard(floor)
        return leaving

    def move_towards(self, direction: int):
        self.current_floor += direction
        self.state = Elevator.MOVING_UP if direction == 1 else Elevator.MOVING_DOWN

    def __repr__(self):
        return (f"Elevator(floor={self.current_floor}, state={self.state}, "
                f"load={self.load}/{self.capacity})")


class Controller:
    """
    مغز سیستم: تصمیم می‌گیرد آسانسور در چه جهتی حرکت کند و کجا توقف کند.
    الگوریتم: SCAN (Elevator Algorithm) - در یک جهت حرکت می‌کند تا
    دیگر درخواستی در آن جهت (نه از بیرون، نه از داخل) نباشد، سپس جهت را عوض می‌کند.
    """

    def __init__(self, building: "Building"):
        self.building = building
        self.elevator = building.elevator
        self.log: list[str] = []

    def _has_any_request_ahead(self, direction: int) -> bool:
        """آیا در جهت داده‌شده، از موقعیت فعلی به بعد، درخواستی (داخلی یا بیرونی) هست؟"""
        cur = self.elevator.current_floor
        floors_range = (
            range(cur, NUM_FLOORS) if direction == 1 else range(cur, -1, -1)
        )
        for f in floors_range:
            if f in self.elevator.target_floors:
                return True
            floor_obj = self.building.floors[f]
            if floor_obj.has_request(direction):
                return True
        return False

    def _has_any_request_anywhere(self) -> bool:
        if self.elevator.target_floors:
            return True
        return any(f.waiting_up or f.waiting_down for f in self.building.floors)

    def step(self, now: float):
        """یک گام زمانی شبیه‌سازی: تصمیم بگیر و آسانسور را جابه‌جا کن."""
        elevator = self.elevator
        cur = elevator.current_floor
        floor_obj = self.building.floors[cur]

        # 1) اگر در این طبقه کسی باید پیاده شود، پیاده کن
        left = elevator.unload_at(cur, now)
        if left:
            self.log.append(f"t={now}: طبقه {cur} -> پیاده شدند: {left}")

        # 2) تعیین جهت فعلی در صورت IDLE بودن
        if elevator.state == Elevator.IDLE:
            if self._has_any_request_ahead(1):
                elevator.state = Elevator.MOVING_UP
            elif self._has_any_request_ahead(-1):
                elevator.state = Elevator.MOVING_DOWN
            elif not self._has_any_request_anywhere():
                self.log.append(f"t={now}: آسانسور بیکار در طبقه {cur}")
                return

        direction = 1 if elevator.state == Elevator.MOVING_UP else -1

        # 3) سوار کردن افرادی که هم‌جهت‌اند و ظرفیت هست
        if floor_obj.has_request(direction) and elevator.free_capacity > 0:
            boarding = floor_obj.pop_boarding(direction, elevator.free_capacity)
            if boarding:
                elevator.board(boarding, now)
                self.log.append(f"t={now}: طبقه {cur} -> سوار شدند: {boarding}")

        # 4) بررسی ادامه مسیر در همین جهت یا معکوس کردن جهت
        if not self._has_any_request_ahead(direction):
            opposite = -direction
            if self._has_any_request_ahead(opposite):
                direction = opposite
                elevator.state = Elevator.MOVING_UP if direction == 1 else Elevator.MOVING_DOWN
            elif not self._has_any_request_anywhere():
                elevator.state = Elevator.IDLE
                return

        # 5) حرکت یک طبقه در جهت انتخاب‌شده (اگر به انتهای ساختمان نرسیده باشیم)
        next_floor = cur + direction
        if 0 <= next_floor <= NUM_FLOORS - 1:
            elevator.move_towards(direction)
            self.log.append(f"t={now}: آسانسور حرکت کرد به طبقه {elevator.current_floor}")


class Building:
    """ساختمان: شامل 60 طبقه، یک آسانسور و یک کنترلر."""

    def __init__(self, num_floors: int = NUM_FLOORS, capacity: int = 8):
        self.num_floors = num_floors
        self.floors = [Floor(i) for i in range(num_floors)]
        self.elevator = Elevator(capacity=capacity)
        self.controller = Controller(self)
        self.people: list[Person] = []
        self.clock = 0

    def request(self, origin: int, destination: int):
        p = Person(origin, destination, self.clock)
        self.people.append(p)
        self.floors[origin].add_request(p)
        return p

    def tick(self):
        self.clock += 1
        self.controller.step(self.clock)

    def average_wait_time(self):
        waits = [p.wait_time for p in self.people if p.wait_time is not None]
        return sum(waits) / len(waits) if waits else None


if __name__ == "__main__":
    # تست سریع منطق بدون GUI
    random.seed(0)
    b = Building()
    print(f"ساختمان با {b.num_floors} طبقه ساخته شد.")

    # چند درخواست تصادفی
    for _ in range(5):
        origin = random.randint(0, b.num_floors - 1)
        dest = random.randint(0, b.num_floors - 1)
        while dest == origin:
            dest = random.randint(0, b.num_floors - 1)
        p = b.request(origin, dest)
        print("درخواست جدید:", p)

    for _ in range(400):
        b.tick()

    print("\n--- لاگ حرکت آسانسور ---")
    for line in b.controller.log:
        print(line)

    print("\nمیانگین زمان انتظار:", b.average_wait_time())
    for p in b.people:
        print(p, "wait:", p.wait_time, "travel:", p.travel_time)


class ElevatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"شبیه‌ساز آسانسور هوشمند  (a={A}, ساختمان {NUM_FLOORS} طبقه)")

        self.building = Building(num_floors=NUM_FLOORS, capacity=8)
        self.running = False

        self._build_layout()
        self._draw_static_floors()
        self._draw_elevator()
        self._refresh_status()

    # ---------------------------------------------------------------
    # ساخت رابط کاربری
    # ---------------------------------------------------------------
    def _build_layout(self):
        main = ttk.Frame(self.root, padding=8)
        main.pack(fill="both", expand=True)

        # --- ستون چپ: کانواس اسکرول‌شونده ساختمان ---
        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True)

        canvas_frame = ttk.Frame(left)
        canvas_frame.pack(fill="both", expand=True)

        self.canvas_height_total = NUM_FLOORS * FLOOR_HEIGHT + 20
        self.canvas = tk.Canvas(
            canvas_frame, width=CANVAS_WIDTH, height=500,
            bg="white", scrollregion=(0, 0, CANVAS_WIDTH, self.canvas_height_total)
        )
        vbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=vbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        vbar.pack(side="right", fill="y")
        # پیش‌فرض روی پایین‌ترین طبقه (لابی) اسکرول کن
        self.canvas.yview_moveto(1.0)

        # --- ستون راست: کنترل‌ها و وضعیت ---
        right = ttk.Frame(main, padding=(10, 0))
        right.pack(side="right", fill="y")

        ttk.Label(right, text="احضار آسانسور از طبقه", font=("Tahoma", 11, "bold")).pack(pady=(0, 4))
        call_frame = ttk.Frame(right)
        call_frame.pack(pady=4)
        ttk.Label(call_frame, text="طبقه:").grid(row=0, column=0, padx=2)
        self.call_floor_var = tk.IntVar(value=0)
        ttk.Spinbox(call_frame, from_=0, to=NUM_FLOORS - 1, width=6,
                    textvariable=self.call_floor_var).grid(row=0, column=1, padx=2)
        ttk.Label(call_frame, text="مقصد:").grid(row=1, column=0, padx=2, pady=4)
        self.call_dest_var = tk.IntVar(value=NUM_FLOORS - 1)
        ttk.Spinbox(call_frame, from_=0, to=NUM_FLOORS - 1, width=6,
                    textvariable=self.call_dest_var).grid(row=1, column=1, padx=2, pady=4)
        ttk.Button(right, text="ثبت درخواست", command=self.on_new_request).pack(pady=6, fill="x")
        ttk.Button(right, text="۵ درخواست تصادفی", command=self.on_random_requests).pack(pady=2, fill="x")

        ttk.Separator(right, orient="horizontal").pack(fill="x", pady=10)

        ttk.Label(right, text="کنترل شبیه‌سازی", font=("Tahoma", 11, "bold")).pack(pady=(0, 4))
        btns = ttk.Frame(right)
        btns.pack()
        self.start_btn = ttk.Button(btns, text="شروع ▶", command=self.on_start)
        self.start_btn.grid(row=0, column=0, padx=3)
        self.stop_btn = ttk.Button(btns, text="توقف ⏸", command=self.on_stop, state="disabled")
        self.stop_btn.grid(row=0, column=1, padx=3)
        ttk.Button(btns, text="یک گام ⏭", command=self.on_single_step).grid(row=0, column=2, padx=3)

        ttk.Separator(right, orient="horizontal").pack(fill="x", pady=10)

        ttk.Label(right, text="وضعیت", font=("Tahoma", 11, "bold")).pack(pady=(0, 4))
        self.status_text = tk.Text(right, width=32, height=14, state="disabled",
                                    font=("Consolas", 9))
        self.status_text.pack()

    # ---------------------------------------------------------------
    # رسم اولیه طبقات (ثابت، فقط یک بار)
    # ---------------------------------------------------------------
    def _y_of_floor(self, floor_number: int) -> int:
        """تبدیل شماره طبقه به مختصات y روی کانواس (طبقه 0 پایین‌ترین است)."""
        return (NUM_FLOORS - 1 - floor_number) * FLOOR_HEIGHT + 10

    def _draw_static_floors(self):
        for f in range(NUM_FLOORS):
            y = self._y_of_floor(f)
            self.canvas.create_line(0, y, CANVAS_WIDTH, y, fill="#dddddd")
            label = "لابی" if f == 0 else str(f)
            self.canvas.create_text(20, y + FLOOR_HEIGHT / 2, text=label,
                                     font=("Tahoma", 8), anchor="w")
        # چاه آسانسور
        self.canvas.create_line(SHAFT_X0, 0, SHAFT_X0, self.canvas_height_total, fill="#888888")
        self.canvas.create_line(SHAFT_X1, 0, SHAFT_X1, self.canvas_height_total, fill="#888888")

        # نشانگرهای درخواست (up/down) - آبجکت‌های پویا در دیکشنری نگه داشته می‌شوند
        self.request_markers = {}  # floor -> canvas item id

    def _draw_elevator(self):
        y = self._y_of_floor(self.building.elevator.current_floor)
        self.elevator_rect = self.canvas.create_rectangle(
            SHAFT_X0 + 4, y + 2, SHAFT_X1 - 4, y + FLOOR_HEIGHT - 2,
            fill="#4a90d9", outline="#2c5d8a", width=2
        )
        self.elevator_label = self.canvas.create_text(
            (SHAFT_X0 + SHAFT_X1) / 2, y + FLOOR_HEIGHT / 2,
            text="0", fill="white", font=("Tahoma", 8, "bold")
        )

    # ---------------------------------------------------------------
    # رویدادهای کاربر
    # ---------------------------------------------------------------
    def on_new_request(self):
        origin = self.call_floor_var.get()
        dest = self.call_dest_var.get()
        if origin == dest:
            messagebox.showwarning("خطا", "طبقه مبدأ و مقصد نباید یکسان باشند.")
            return
        p = self.building.request(origin, dest)
        self._update_request_marker(origin)
        self._refresh_status(f"درخواست جدید ثبت شد: {p}")

    def on_random_requests(self):
        for _ in range(5):
            origin = random.randint(0, NUM_FLOORS - 1)
            dest = random.randint(0, NUM_FLOORS - 1)
            while dest == origin:
                dest = random.randint(0, NUM_FLOORS - 1)
            p = self.building.request(origin, dest)
            self._update_request_marker(origin)
        self._refresh_status("۵ درخواست تصادفی اضافه شد.")

    def on_start(self):
        self.running = True
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self._loop()

    def on_stop(self):
        self.running = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")

    def on_single_step(self):
        self._simulate_one_tick()

    # ---------------------------------------------------------------
    # حلقه شبیه‌سازی
    # ---------------------------------------------------------------
    def _loop(self):
        if not self.running:
            return
        self._simulate_one_tick()
        self.root.after(TICK_MS, self._loop)

    def _simulate_one_tick(self):
        prev_targets = set()
        for f in self.building.floors:
            if f.waiting_up:
                prev_targets.add((f.number, 1))
            if f.waiting_down:
                prev_targets.add((f.number, -1))

        self.building.tick()

        self._redraw_elevator()
        self._refresh_request_markers()
        self._refresh_status()

    # ---------------------------------------------------------------
    # به‌روزرسانی نمایش
    # ---------------------------------------------------------------
    def _redraw_elevator(self):
        y = self._y_of_floor(self.building.elevator.current_floor)
        self.canvas.coords(self.elevator_rect, SHAFT_X0 + 4, y + 2, SHAFT_X1 - 4, y + FLOOR_HEIGHT - 2)
        self.canvas.coords(self.elevator_label, (SHAFT_X0 + SHAFT_X1) / 2, y + FLOOR_HEIGHT / 2)
        load = self.building.elevator.load
        self.canvas.itemconfigure(self.elevator_label, text=str(load))
        # اسکرول خودکار به سمت آسانسور
        frac = 1 - (self.building.elevator.current_floor / max(1, NUM_FLOORS - 1))
        self.canvas.yview_moveto(max(0.0, min(1.0, frac - 0.15)))

    def _update_request_marker(self, floor_number: int):
        y = self._y_of_floor(floor_number)
        if floor_number in self.request_markers:
            self.canvas.delete(self.request_markers[floor_number])
        marker = self.canvas.create_oval(
            SHAFT_X1 + 10, y + 4, SHAFT_X1 + 18, y + FLOOR_HEIGHT - 4,
            fill="orange", outline="red"
        )
        self.request_markers[floor_number] = marker

    def _refresh_request_markers(self):
        for f in self.building.floors:
            has_req = bool(f.waiting_up or f.waiting_down)
            if not has_req and f.number in self.request_markers:
                self.canvas.delete(self.request_markers[f.number])
                del self.request_markers[f.number]

    def _refresh_status(self, message: str = None):
        e = self.building.elevator
        avg_wait = self.building.average_wait_time()
        avg_wait_str = f"{avg_wait:.1f}" if avg_wait is not None else "—"
        lines = [
            f"زمان شبیه‌سازی: {self.building.clock}",
            f"طبقه فعلی آسانسور: {e.current_floor}",
            f"وضعیت: {e.state}",
            f"تعداد مسافران داخل: {e.load}/{e.capacity}",
            f"مقاصد در صف داخل آسانسور: {sorted(e.target_floors)}",
            f"تعداد کل درخواست‌ها: {len(self.building.people)}",
            f"میانگین زمان انتظار: {avg_wait_str}",
        ]
        if message:
            lines.append("")
            lines.append(message)

        self.status_text.configure(state="normal")
        self.status_text.delete("1.0", "end")
        self.status_text.insert("1.0", "\n".join(lines))
        self.status_text.configure(state="disabled")


def main():
    root = tk.Tk()
    app = ElevatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
