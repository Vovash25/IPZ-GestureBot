import tkinter as tk
from multiprocessing import Process, Value, Event, Queue
import time
import queue

from blockstest import run_display
from visual_module import run_vision
from robot_module import run_robot

class RobotApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Industrial Robot Control HMI")
        self.geometry("450x700")

        self.conveyor_running = Event()
        self.conveyor_speed = Value('i', 5)
        self.app_mode = Value('i', 0)

        self.coord_queue = Queue()
        self.setup_ui()
        self.start_systems()
        self.update_log_from_queue()

    def setup_ui(self):
        tk.Label(self, text="CONTROL PANEL", font=("Arial", 24, "bold")).pack(pady=20)
        tk.Label(self, text="SELECT MODE", font=("Arial", 12)).pack()

        self.mode_var = tk.StringVar(value="Conveyor")
        frame_modes = tk.Frame(self)
        frame_modes.pack(pady=10)

        tk.Radiobutton(frame_modes, text="Conveyor", variable=self.mode_var, value="Conveyor",
                       command=self.change_mode, font=("Arial", 12)).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(frame_modes, text="Manual Sort", variable=self.mode_var, value="Manual Sort",
                       command=self.change_mode, font=("Arial", 12)).pack(side=tk.LEFT, padx=10)

        self.status_label = tk.Label(self, text="CONVEYOR: STOPPED", fg="red", font=("Arial", 16, "bold"))
        self.status_label.pack(pady=10)

        self.btn_start = tk.Button(self, text="START CONVEYOR", bg="green", fg="white",
                                   font=("Arial", 12, "bold"), width=20, command=self.start_conveyor)
        self.btn_start.pack(pady=5)

        self.btn_stop = tk.Button(self, text="STOP CONVEYOR", bg="darkred", fg="white",
                                  font=("Arial", 12, "bold"), width=20, command=self.stop_conveyor)
        self.btn_stop.pack(pady=5)

        tk.Label(self, text="CONVEYOR SPEED", font=("Arial", 12)).pack(pady=(20, 0))
        self.speed_slider = tk.Scale(self, from_=2, to=25, orient=tk.HORIZONTAL, length=300, command=self.update_speed)
        self.speed_slider.set(5)
        self.speed_slider.pack(pady=10)

        self.log_box = tk.Text(self, width=50, height=15, font=("Arial", 10))
        self.log_box.pack(pady=20)

    def change_mode(self):
        value = self.mode_var.get()
        if value == "Conveyor":
            self.app_mode.value = 0
            self.btn_start.configure(state="normal")
            self.btn_stop.configure(state="normal")
        else:
            self.app_mode.value = 1
            self.btn_start.configure(state="disabled")
            self.btn_stop.configure(state="disabled")

    def start_systems(self):
        self.p_vision = Process(target=run_vision, args=(self.coord_queue,))
        self.p_vision.start()

        self.p_display = Process(target=run_display, args=(self.conveyor_running, self.conveyor_speed, self.app_mode))
        self.p_display.start()

        self.p_robot = Process(target=run_robot, args=(self.coord_queue,))
        self.p_robot.start()

    def update_log_from_queue(self):
        try:
            while True:
                msg = self.coord_queue.get_nowait()
                self.log_box.insert("1.0", f"{msg}\n")
        except queue.Empty:
            pass
        self.after(100, self.update_log_from_queue)

    def start_conveyor(self):
        self.conveyor_running.set()
        self.status_label.configure(text="CONVEYOR: RUNNING", fg="green")

    def stop_conveyor(self):
        self.conveyor_running.clear()
        self.status_label.configure(text="CONVEYOR: STOPPED", fg="red")

    def update_speed(self, val):
        self.conveyor_speed.value = int(float(val))

if __name__ == "__main__":
    app = RobotApp()
    app.mainloop()
