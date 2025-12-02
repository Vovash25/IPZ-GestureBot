import numpy as np
import matplotlib.pyplot as plt


L1, L2 = 150.0, 130.0  # Reka 1
L1b, L2b = 150.0, 130.0  # Reka 2

base1_pos = np.array([-100.0, 0.0])
base2_pos = np.array([100.0, 0.0])


SCREEN_WIDTH = 287.3
SCREEN_HEIGHT = 69.8

SCREEN_Y_OFFSET = 190.0
SCREEN_X_START = -SCREEN_WIDTH / 2


class SCARA:
    def __init__(self, L1, L2):
        self.L1 = L1
        self.L2 = L2

    def fk(self, t1, t2):
        x = self.L1 * np.cos(t1) + self.L2 * np.cos(t1 + t2)
        y = self.L1 * np.sin(t1) + self.L2 * np.sin(t1 + t2)
        return np.array([x, y])

    def ik(self, x, y, elbow_up=True):
        r2 = x ** 2 + y ** 2
        cos_t2 = (r2 - self.L1 ** 2 - self.L2 ** 2) / (2 * self.L1 * self.L2)
        if abs(cos_t2) > 1:
            return None, None

        sin_t2 = np.sqrt(1 - cos_t2 ** 2)
        if not elbow_up:
            sin_t2 = -sin_t2
        t2 = np.arctan2(sin_t2, cos_t2)

        t1 = np.arctan2(y, x) - np.arctan2(self.L2 * np.sin(t2), self.L1 + self.L2 * np.cos(t2))
        return t1, t2



def plot_two_arms_shared_target(arm1, arm2, base1, base2, target):
    plt.figure(figsize=(10, 8))
    plt.grid(True)
    plt.gca().set_aspect('equal', 'box')
    plt.title("Symulator: Maksymalny Zasięg i Ekran (Y_max = 261.5 mm)")


    screen_rect = plt.Rectangle((SCREEN_X_START, SCREEN_Y_OFFSET),
                                SCREEN_WIDTH, SCREEN_HEIGHT,
                                facecolor='#d0e0ff', edgecolor='black',
                                alpha=0.8,
                                label=f'Ekran (Y od {SCREEN_Y_OFFSET:.1f} do {SCREEN_Y_OFFSET + SCREEN_HEIGHT:.1f})')
    plt.gca().add_patch(screen_rect)

    # ramię 1
    target_local1 = target - base1
    t1_1, t2_1 = arm1.ik(*target_local1)

    if t1_1 is None:
        print(f"Cel X={target[0]}, Y={target[1]} jest nieosiągalny dla ramienia 1. Przerwano.")
        return

    joint1_1_local = np.array([arm1.L1 * np.cos(t1_1), arm1.L1 * np.sin(t1_1)])
    joint1_1_global = base1 + joint1_1_local

    plt.plot([base1[0], joint1_1_global[0]], [base1[1], joint1_1_global[1]], 'b-', lw=5, label='L1')
    plt.plot([joint1_1_global[0], target[0]], [joint1_1_global[1], target[1]], 'b--', lw=5)
    plt.plot(base1[0], base1[1], 'bs', ms=10, label='Baza 1')

    # ramię 2
    target_local2 = target - base2
    t1_2, t2_2 = arm2.ik(*target_local2)

    if t1_2 is None:
        print(f"Cel X={target[0]}, Y={target[1]} jest nieosiągalny dla ramienia 2. Przerwano.")
        return

    joint1_2_local = np.array([arm2.L1 * np.cos(t1_2), arm2.L1 * np.sin(t1_2)])
    joint1_2_global = base2 + joint1_2_local

    plt.plot([base2[0], joint1_2_global[0]], [base2[1], joint1_2_global[1]], 'r-', lw=5, label='L1b')
    plt.plot([joint1_2_global[0], target[0]], [joint1_2_global[1], target[1]], 'r--', lw=5)
    plt.plot(base2[0], base2[1], 'rs', ms=10, label='Baza 2')


    plt.plot(target[0], target[1], 'kx', ms=15, mew=4, label=f'Wspólny Cel ({target[0]}, {target[1]})')
    plt.plot(target[0], target[1], 'bo', ms=8)
    plt.plot(target[0], target[1], 'ro', ms=8)


    plt.xlim(SCREEN_X_START - 20, SCREEN_X_START + SCREEN_WIDTH + 20)
    plt.ylim(base1[1] - 10, SCREEN_Y_OFFSET + SCREEN_HEIGHT + 50)

    plt.xlabel("X (mm)")
    plt.ylabel("Y (mm)")
    plt.legend(loc='lower left')
    plt.show()




if __name__ == '__main__':
    arm1 = SCARA(L1, L2)
    arm2 = SCARA(L1b, L2b)

    print("--- Symulator: Ekran na Granicy Zasięgu (Y_max) ---")
    print(f"Maksymalny wysięg w osi Y: 261.5 mm.")
    print(f"Ekran znajduje się w zakresie Y=[{SCREEN_Y_OFFSET:.1f}, {SCREEN_Y_OFFSET + SCREEN_HEIGHT:.1f}] mm.")
    print("Wprowadź współrzędne X Y celu ruchu lub 'q', aby zakończyć program.")

    while True:
        user = input("Podaj X Y: ").strip()
        if user.lower() == 'q':
            break
        try:
            x, y = map(float, user.split())
            target = np.array([x, y])


            if y > SCREEN_Y_OFFSET + SCREEN_HEIGHT:
                print("!!! Uwaga: Cel znajduje się poza fizycznym obszarem pracy (Y > 261.5 mm) !!!")

            plot_two_arms_shared_target(arm1, arm2, base1_pos, base2_pos, target)

        except ValueError:
            print("Błędne dane. Wprowadź dwie liczby (X Y).")
        except Exception as e:
            print(f"Wystąpił błąd: {e}")
