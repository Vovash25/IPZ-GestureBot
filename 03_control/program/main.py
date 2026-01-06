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
SCR_W, SCR_H, SCR_Y = 287.3, 69.8, 290.0

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("SCARA Fixed Logic")
        
        self.brain = RobotBrain(L1, L2, BASE_L, BASE_R)
        self.shapes = [Shape(0, SCR_Y + 30)]
        self.scale = 1.1
        self.last_click_time = 0
        self.click_count = 0

        self.setup_ui()
        self.draw_loop()

    def setup_ui(self):
        self.info_label = tk.Label(self.root, text="COORD -> X: 0.0 | Y: 300.0", 
                                   font=("Courier", 11), bg="#1e1e1e", fg="#00ff00")
        self.info_label.pack(side="top", fill="x")

        self.canvas = tk.Canvas(self.root, width=800, height=750, bg="#1a1a1a", highlightthickness=0)
        self.canvas.pack()
        
        ui = ttk.Frame(self.root)
        ui.pack(pady=10)
        
        self.btn_auto = ttk.Button(ui, text="START AUTO", command=self.toggle_auto)
        self.btn_auto.grid(row=0, column=0, padx=5)
        ttk.Button(ui, text="ADD OBJ", command=self.add_shape).grid(row=0, column=1, padx=5)
        ttk.Button(ui, text="RESET", command=self.reset).grid(row=0, column=2, padx=5)

        
        self.canvas.bind("<Button-1>", self.handle_press)
        self.canvas.bind("<B1-Motion>", self.handle_motion)
        self.canvas.bind("<ButtonRelease-1>", self.handle_release)

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
            time.sleep(0.5)

    def handle_press(self, event):
        if self.brain.auto_mode: return
        mx, my = (event.x - 400)/self.scale, (700 - event.y)/self.scale
        
        
        now = time.time()
        if now - self.last_click_time < 0.4: self.click_count += 1
        else: self.click_count = 1
        self.last_click_time = now

        
        hit = None
        for s in self.shapes:
            if np.hypot(s.x - mx, s.y - my) < 30: 
                hit = s; break
        self.brain.selected_shape = hit

        
        if self.brain.compute_all_ik(mx, my):
            self.brain.path_history.append((mx, my))
            self.update_info(mx, my)

        if hit and self.click_count == 3:
            threading.Thread(target=self.brain.triple_tap_sync, args=(self.shapes,), daemon=True).start()

    def handle_motion(self, event):
        if self.brain.auto_mode: return
        mx, my = (event.x - 400)/self.scale, (700 - event.y)/self.scale
        
        if self.brain.compute_all_ik(mx, my):
            self.brain.is_down = True
            self.brain.path_history.append((mx, my))
            
            if self.brain.selected_shape:
                if self.click_count == 2: 
                    self.brain.selected_shape.angle += (mx - self.brain.selected_shape.x) * 2
                else: 
                    self.brain.selected_shape.x = np.clip(mx, -SCR_W/2, SCR_W/2)
                    self.brain.selected_shape.y = np.clip(my, SCR_Y, SCR_Y+SCR_H)
            self.update_info(mx, my)

    def handle_release(self, event):
        self.brain.is_down = False

    def update_info(self, x, y):
        self.info_label.config(text=f"COORD -> X: {x:6.1f} | Y: {y:6.1f} | REACH: {np.hypot(x,y):.1f}/445")

    def add_shape(self):
        self.shapes.append(Shape(random.randint(-100, 100), random.randint(300, 340)))

    def reset(self):
        self.brain.auto_mode = False
        self.shapes = [Shape(0, 320)]
        self.brain.path_history = [(0.0, 300.0)]
        self.btn_auto.config(text="START AUTO")

    def draw_loop(self):
        self.canvas.delete("all")
        
        rmax = (L1 + L2) * self.scale
        for base in [BASE_L, BASE_R]:
            cx, cy = 400 + base[0]*self.scale, 700 - base[1]*self.scale
            self.canvas.create_oval(cx-rmax, cy-rmax, cx+rmax, cy+rmax, outline="#333", dash=(2,2))

        ex = 400 + (-SCR_W/2)*self.scale
        ey = 700 - (SCR_Y+SCR_H)*self.scale
        self.canvas.create_rectangle(ex, ey, ex+SCR_W*self.scale, ey+SCR_H*self.scale, fill="#222", outline="#555")
        
        for s in self.shapes:
            px, py = 400 + s.x*self.scale, 700 - s.y*self.scale
            sz = 12 * self.scale
            outline = "white" if s == self.brain.selected_shape else ""
            rad = np.deg2rad(s.angle); c, st = np.cos(rad), np.sin(rad)
            pts = []
            for dx, dy in [(-10,-10), (10,-10), (10,10), (-10,10)]:
                pts.append(px + (dx*c - dy*st)*self.scale)
                pts.append(py + (dx*st + dy*c)*self.scale)
            self.canvas.create_polygon(pts, fill=s.color, outline=outline, width=2)

        tx, ty = self.brain.path_history[-1]
        res = self.brain.compute_all_ik(tx, ty)
        if res:
            for base, angles, color in zip([BASE_L, BASE_R], res, ["#3498db", "#e74c3c"]):
                self.draw_arm(base, angles, color)
        
        px, py = 400 + tx*self.scale, 700 - ty*self.scale
        color = "yellow" if self.brain.is_down else "white"
        self.canvas.create_oval(px-8, py-8, px+8, py+8, fill=color, outline="black")
        
        self.root.after(20, self.draw_loop)

    def draw_arm(self, base, angles, color):
        t1, t2 = angles
        p1 = base + np.array([L1*np.cos(t1), L1*np.sin(t1)])
        p2 = p1 + np.array([L2*np.cos(t1+t2), L2*np.sin(t1+t2)])
        pts = [400+base[0]*self.scale, 700-base[1]*self.scale, 400+p1[0]*self.scale, 700-p1[1]*self.scale, 400+p2[0]*self.scale, 700-p2[1]*self.scale]
        self.canvas.create_line(pts[:4], fill=color, width=12, capstyle="round")
        self.canvas.create_line(pts[2:], fill=color, width=7, capstyle="round")

if __name__ == '__main__':
    root = tk.Tk()
    App(root)
    root.mainloop()