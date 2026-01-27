import time
import threading
import numpy as np
from kinematics import SCARAKinematics

MAX_PATH = 200

class RobotBrain:
    def __init__(self, l1, l2, base_l, base_r):
        self.kin = SCARAKinematics(l1, l2)
        self.l1, self.l2 = l1, l2
        self.base_l = base_l
        self.base_r = base_r
        self.path_history = [(0.0, 300.0)]
        self.is_down = False
        self.auto_mode = False
        self.selected_shape = None
        self.lock = threading.Lock()
        self.update_callback = None
        self.last_ik = None

    def compute_all_ik(self, x, y):
        l = self.kin.ik(x - self.base_l[0], y - self.base_l[1], elbow_up=False)
        r = self.kin.ik(x - self.base_r[0], y - self.base_r[1], elbow_up=True)
        if l and r and l[0] is not None and r[0] is not None:
            self.last_ik = (l, r)
            return self.last_ik
        return None

    def move_to(self, tx, ty, steps=11):
        if not self.lock.acquire(blocking=False): return
        try:
            sx, sy = self.path_history[-1]
            for i in range(steps):
                t = i / steps
                t = t * t * (3 - 2 * t)  # smoothstep
                px = sx + (tx - sx) * t
                py = sy + (ty - sy) * t
                if self.compute_all_ik(px, py):
                    self.path_history.append((px, py))
                    if len(self.path_history) > MAX_PATH:
                        self.path_history.pop(0)
        finally:
            self.lock.release()

    def move_to_sync(self, tx, ty, steps=20):
        sx, sy = self.path_history[-1]
        for i in range(steps + 1):
            if not self.auto_mode and self.selected_shape: break
            t = i / steps
            t = t * t * (3 - 2 * t)  # smoothstep
            px = sx + (tx - sx) * t
            py = sy + (ty - sy) * t
            if self.compute_all_ik(px, py):
                self.path_history.append((px, py))
                if len(self.path_history) > MAX_PATH:
                    self.path_history.pop(0)

    def triple_tap_sync(self, shapes_list):
        for _ in range(3):
            self.is_down = True; time.sleep(0.12)
            self.is_down = False; time.sleep(0.12)
        if self.selected_shape in shapes_list:
            shapes_list.remove(self.selected_shape)
        self.selected_shape = None
