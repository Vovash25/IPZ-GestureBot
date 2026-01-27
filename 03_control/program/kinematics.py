import numpy as np

class SCARAKinematics:
    def __init__(self, l1, l2):
        self.l1 = l1
        self.l2 = l2

    def ik(self, x, y, elbow_up=True):
        r2 = x**2 + y**2
        if r2 > (self.l1 + self.l2)**2 - 1 or r2 < abs(self.l1 - self.l2)**2 + 1:
            return None, None
        c2 = np.clip((r2 - self.l1**2 - self.l2**2) / (2 * self.l1 * self.l2), -1.0, 1.0)
        s2 = np.sqrt(max(0, 1 - c2**2)) * (1 if elbow_up else -1)
        t2 = np.arctan2(s2, c2)
        t1 = np.arctan2(y, x) - np.arctan2(self.l2 * s2, self.l1 + self.l2 * c2)
        return t1, t2
