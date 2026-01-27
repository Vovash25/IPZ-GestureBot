import tkinter as tk
from tkinter import ttk
import threading
import random
import numpy as np
import time

from models import Shape
from robot_logic import RobotBrain

L1, L2 = 246.0, 199.0
BASE_L, BASE_R = np.array([-120.0, 0.0]), np.array([120.0, 0.0])


class App:
    def __init__(self, root):
        self.root = root
        self.root.withdraw()

        self.brain = RobotBrain(L1, L2, BASE_L, BASE_R)
        # стартовый кубик чуть выше низа
        start_y = L1 * 0.5
        self.shapes = [Shape(0, start_y)]
        self.scale = 1.2
        self.last_click_time = 0
        self.click_count = 0

        # Симулятор
        self.win_sim = tk.Toplevel(root)
        self.win_sim.title("Robot Debugger")
        self.info_label = tk.Label(self.win_sim, text="SYSTEM READY", font=("Courier", 11), bg="#1e1e1e", fg="#00ff00")
        self.info_label.pack(side="top", fill="x")
        self.canvas_sim = tk.Canvas(self.win_sim, width=800, height=750, bg="#1a1a1a", highlightthickness=0)
        self.canvas_sim.pack()

        # UI
        self.win_ui = tk.Toplevel(root)
        self.win_ui.title("Touch Interface (Frontend)")
        self.canvas_ui = tk.Canvas(self.win_ui, bg="#111", highlightthickness=0)
        self.canvas_ui.pack(expand=True, fill="both")

        self.setup_controls()
        self.draw_loop()

    # ----- координаты -----
    def robot_to_canvas_sim(self, x, y):
        return 400 + x * self.scale, 700 - y * self.scale

    def robot_to_canvas_ui(self, x, y):
        w = self.canvas_ui.winfo_width()
        h = self.canvas_ui.winfo_height()
        y_offset = h * 0.78  # “земля” чуть выше низа
        return w / 2 + x * self.scale, y_offset - y * self.scale

    def canvas_ui_to_robot(self, x, y):
        w = self.canvas_ui.winfo_width()
        h = self.canvas_ui.winfo_height()
        y_offset = h * 0.78
        rx = (x - w / 2) / self.scale
        ry = (y_offset - y) / self.scale
        ry = max(0, min(ry, L1 + L2))  # ограничение рабочей зоны
        return rx, ry

    # ----- UI -----
    def setup_controls(self):
        ui_frame = ttk.Frame(self.win_sim)
        ui_frame.pack(pady=10)

        self.btn_auto = ttk.Button(ui_frame, text="START AUTO", command=self.toggle_auto)
        self.btn_auto.grid(row=0, column=0, padx=5)
        ttk.Button(ui_frame, text="ADD OBJ", command=self.add_shape).grid(row=0, column=1, padx=5)
        ttk.Button(ui_frame, text="RESET", command=self.reset).grid(row=0, column=2, padx=5)

        self.canvas_ui.bind("<Button-1>", self.handle_press)
        self.canvas_ui.bind("<B1-Motion>", self.handle_motion)
        self.canvas_ui.bind("<ButtonRelease-1>", self.handle_release)

    def handle_release(self, event):
        self.brain.is_down = False

    def toggle_auto(self):
        self.brain.auto_mode = not self.brain.auto_mode
        self.btn_auto.config(text="STOP AUTO" if self.brain.auto_mode else "START AUTO")
        if self.brain.auto_mode:
            threading.Thread(target=self.auto_loop, daemon=True).start()

    def auto_loop(self):
        while self.brain.auto_mode:
            if self.shapes:
                target = self.shapes[0]
                self.brain.selected_shape = target
                self.brain.move_to_sync(target.x, target.y)
                if self.brain.auto_mode:
                    self.brain.triple_tap_sync(self.shapes)
            time.sleep(0.5)

    # ----- события -----
    def handle_press(self, event):
        if self.brain.auto_mode: return
        mx, my = self.canvas_ui_to_robot(event.x, event.y)

        now = time.time()
        if now - self.last_click_time < 0.4:
            self.click_count += 1
        else:
            self.click_count = 1
        self.last_click_time = now

        hit = None
        for s in self.shapes:
            if np.hypot(s.x - mx, s.y - my) < 40:
                hit = s
                break
        self.brain.selected_shape = hit

        if hit and self.click_count == 3:
            threading.Thread(target=self.brain.triple_tap_sync, args=(self.shapes,), daemon=True).start()

    def handle_motion(self, event):
        if self.brain.auto_mode: return
        mx, my = self.canvas_ui_to_robot(event.x, event.y)

        if self.brain.compute_all_ik(mx, my):
            self.brain.is_down = True
            if self.brain.selected_shape:
                if self.click_count >= 2:
                    dx = mx - self.brain.selected_shape.x
                    self.brain.selected_shape.angle += dx * 5
                else:
                    self.brain.selected_shape.x, self.brain.selected_shape.y = mx, my

            self.info_label.config(
                text=f"ROBOT X: {mx:.1f} Y: {my:.1f} | SHAPE: {'SELECTED' if self.brain.selected_shape else 'NONE'}"
            )

    def add_shape(self):
        # минимальная высота, чтобы кубики не проваливались вниз
        min_y = L1 * 0.3
        max_y = L1 + L2 - 20
        self.shapes.append(Shape(
            random.randint(-400, 400),
            random.randint(int(min_y), int(max_y))
        ))

    def reset(self):
        self.brain.auto_mode = False
        start_y = L1 * 0.5
        self.shapes = [Shape(0, start_y)]
        self.brain.path_history = [(0.0, start_y)]
        self.brain.last_ik = None

    # ----- отрисовка -----
    def draw_loop(self):
        # UI
        self.canvas_ui.delete("all")
        for s in self.shapes:
            px, py = self.robot_to_canvas_ui(s.x, s.y)
            sz = 20 * self.scale
            color = "#00ffcc" if s == self.brain.selected_shape else s.color
            rad = np.deg2rad(s.angle);
            c, st = np.cos(rad), np.sin(rad)
            pts = []
            for dx, dy in [(-1, -1), (1, -1), (1, 1), (-1, 1)]:
                pts.append(px + (dx * sz * c - dy * sz * st))
                pts.append(py + (dx * sz * st + dy * sz * c))
            self.canvas_ui.create_polygon(pts, fill=color, outline="white", width=2)

        # Симулятор
        self.canvas_sim.delete("all")
        ph = self.brain.path_history
        for i in range(1, len(ph)):
            x1, y1 = self.robot_to_canvas_sim(*ph[i - 1])
            x2, y2 = self.robot_to_canvas_sim(*ph[i])
            self.canvas_sim.create_line(x1, y1, x2, y2, fill="#444", width=2)

        rmax = (L1 + L2) * self.scale
        for base in [BASE_L, BASE_R]:
            cx, cy = self.robot_to_canvas_sim(base[0], base[1])
            self.canvas_sim.create_oval(cx - rmax, cy - rmax, cx + rmax, cy + rmax, outline="#222")

        # Точка концевика
        if self.brain.last_ik:
            l_angles, r_angles = self.brain.last_ik
            for base, angles in zip([BASE_L, BASE_R], self.brain.last_ik):
                t1, t2 = angles
                ex = base[0] + L1 * np.cos(t1) + L2 * np.cos(t1 + t2)
                ey = base[1] + L1 * np.sin(t1) + L2 * np.sin(t1 + t2)
                px, py = self.robot_to_canvas_sim(ex, ey)
                self.canvas_sim.create_oval(px - 6, py - 6, px + 6, py + 6, fill="yellow")

        # Руки
        if self.brain.last_ik:
            for base, angles, color in zip([BASE_L, BASE_R], self.brain.last_ik, ["#3498db", "#e74c3c"]):
                self.draw_arm(base, angles, color)

        self.root.after(25, self.draw_loop)

    def draw_arm(self, base, angles, color):
        t1, t2 = angles
        p1 = base + np.array([L1 * np.cos(t1), L1 * np.sin(t1)])
        p2 = p1 + np.array([L2 * np.cos(t1 + t2), L2 * np.sin(t1 + t2)])
        bx, by = self.robot_to_canvas_sim(base[0], base[1])
        p1x, p1y = self.robot_to_canvas_sim(p1[0], p1[1])
        p2x, p2y = self.robot_to_canvas_sim(p2[0], p2[1])
        self.canvas_sim.create_line(bx, by, p1x, p1y, fill=color, width=12, capstyle="round")
        self.canvas_sim.create_line(p1x, p1y, p2x, p2y, fill=color, width=7, capstyle="round")


if __name__ == '__main__':
    root = tk.Tk()
    App(root)
    root.mainloop()
