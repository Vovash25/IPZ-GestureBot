import tkinter as tk
import serial

try:
    arduino = serial.Serial('/dev/ttyUSB0', 115200)
    print("Connected!")
except:
    print("Error! Check USB connection.")

def send_pos(val):
    m1 = scale_m1.get()
    m2 = scale_m2.get()
    cmd = f"M1:{m1},M2:{m2}\n"
    arduino.write(cmd.encode())

root = tk.Tk()
root.title("Axis Calibration")
root.geometry("400x200")

tk.Label(root, text="Left Motor (M1) - Move the slider", font=("Arial", 12)).pack(pady=5)
scale_m1 = tk.Scale(root, from_=0, to=4095, orient=tk.HORIZONTAL, length=350, command=send_pos)
scale_m1.set(2048)
scale_m1.pack()

tk.Label(root, text="Right Motor (M2) - Move the slider", font=("Arial", 12)).pack(pady=5)
scale_m2 = tk.Scale(root, from_=0, to=4095, orient=tk.HORIZONTAL, length=350, command=send_pos)
scale_m2.set(2048)
scale_m2.pack()

root.mainloop()
