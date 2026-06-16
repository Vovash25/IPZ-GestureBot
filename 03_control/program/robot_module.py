import time
import re
import math
import serial

BASE_D = 100.0
L1 = 140.0
L2 = 190.0

M1_X = -BASE_D / 2.0
M1_Y = 0.0
M2_X = BASE_D / 2.0
M2_Y = 0.0

def calculate_ik(target_x, target_y):
    dx1 = target_x - M1_X
    dy1 = target_y - M1_Y
    d1 = math.hypot(dx1, dy1)

    dx2 = target_x - M2_X
    dy2 = target_y - M2_Y
    d2 = math.hypot(dx2, dy2)

    if d1 > (L1 + L2) or d2 > (L1 + L2):
        return None, None
    if d1 < abs(L1 - L2) or d2 < abs(L1 - L2):
        return None, None

    alpha1 = math.atan2(dy1, dx1)
    beta1 = math.acos((d1**2 + L1**2 - L2**2) / (2 * L1 * d1))
    angle_m1_rad = alpha1 + beta1

    alpha2 = math.atan2(dy2, dx2)
    beta2 = math.acos((d2**2 + L1**2 - L2**2) / (2 * L1 * d2))
    angle_m2_rad = alpha2 - beta2

    return math.degrees(angle_m1_rad), math.degrees(angle_m2_rad)


M1_CENTER = 2524
M2_CENTER = 2048

def degrees_to_steps(degrees, is_left_motor):
    if is_left_motor:
        steps = int(M1_CENTER + ((degrees - 90.0) / 360.0) * 4096)
    else:
        steps = int(M2_CENTER + ((degrees - 90.0) / 360.0) * 4096)
    return max(0, min(4095, steps))


def run_robot(coord_queue):
    print("Robot module starting...")

    try:
        arduino = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
        time.sleep(2)
        print("Robot connected via USB successfully!")
    except Exception as e:
        print(f"WARNING: Robot board not found ({e}).")
        arduino = None

    while True:
        if not coord_queue.empty():
            msg = coord_queue.get()

            match = re.search(r'X:(\d+)\s+Y:(\d+)', msg)
            if match:
                pixel_x = int(match.group(1))
                pixel_y = int(match.group(2))

                table_width_mm = 268.2
                table_height_mm = 58.0
                offset_y = 100.0

                scale_x_factor = 1.0
                scale_y_factor = 1.0
                camera_shift_x = 0.0

                corrected_pixel_y = 320.0 - pixel_y

                target_x = ((pixel_x / 1480.0) * table_width_mm - (table_width_mm / 2.0)) * scale_x_factor + camera_shift_x
                target_y = ((corrected_pixel_y / 320.0) * table_height_mm) * scale_y_factor + offset_y

                ang_left, ang_right = calculate_ik(target_x, target_y)

                if ang_left is not None:
                    step1 = degrees_to_steps(ang_left, True)
                    step2 = degrees_to_steps(ang_right, False)

                    command = f"M1:{step1},M2:{step2}\n"
                    print(f"Target: {target_x:.1f}x{target_y:.1f} mm -> Angles: L:{ang_left:.1f} R:{ang_right:.1f} -> Sending: {command.strip()}")

                    if arduino:
                        arduino.write(command.encode('utf-8'))

        time.sleep(0.02)
