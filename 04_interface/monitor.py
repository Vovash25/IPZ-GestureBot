import sys
import random
import time
import math
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt5.QtGui import QPainter, QColor, QPolygon, QPen
from PyQt5.QtCore import Qt, QPoint, QTimer


# ================================================
#   SHAPE CLASS
# ================================================

class Shape:
    def __init__(self, x, y, size, color, shape_type, angle, speed):
        self.x = x
        self.y = y
        self.size = size
        self.color = color
        self.shape_type = shape_type
        self.angle = angle
        self.speed = speed

        # Gesture states
        self.selected = False
        self.grabbed = False      # long press mode
        self.drag_mode = False    # drag mode
        self.last_press_times = []


# ================================================
#   MAIN WIDGET (CONVEYOR + INTERACTION)
# ================================================

class ConveyorWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.shapes = []
        self.active_shape = None

        self.last_x = None
        self.last_y = None

        # Long press detection timer
        self.long_press_timer = QTimer()
        self.long_press_timer.setSingleShot(True)
        self.long_press_timer.timeout.connect(self.enable_grab)

        # Conveyor movement
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_conveyor)
        self.timer.start(30)

        # Spawn shapes
        self.spawn_timer = QTimer()
        self.spawn_timer.timeout.connect(self.spawn_shape)
        self.spawn_timer.start(1500)

    # ---------------------------------------------------
    # SPAWN RANDOM SHAPE
    # ---------------------------------------------------
    def spawn_shape(self):
        shape = Shape(
            x=-150,
            y=random.randint(120, self.height() - 120),
            size=random.randint(30, 60),
            color=QColor(random.randint(50, 250),
                         random.randint(50, 250),
                         random.randint(50, 250)),
            shape_type=random.choice(["circle", "square", "triangle"]),
            angle=random.randint(0, 360),
            speed=random.randint(2, 5)
        )
        self.shapes.append(shape)
        print(f"[SPAWN] {shape.shape_type}, angle={shape.angle}, y={shape.y}")

    # ---------------------------------------------------
    # COLLISION DETECTION
    # ---------------------------------------------------
    def check_collisions(self):
        for i in range(len(self.shapes)):
            for j in range(i + 1, len(self.shapes)):
                a = self.shapes[i]
                b = self.shapes[j]

                dx = a.x - b.x
                dy = a.y - b.y
                distance = math.sqrt(dx * dx + dy * dy)
                min_dist = a.size + b.size

                if distance < min_dist:
                    overlap = min_dist - distance
                    if distance != 0:
                        push_x = (dx / distance) * (overlap / 2)
                        push_y = (dy / distance) * (overlap / 2)
                    else:
                        push_x = push_y = overlap / 2

                    a.x += push_x
                    a.y += push_y
                    b.x -= push_x
                    b.y -= push_y

    # ---------------------------------------------------
    # CONVEYOR UPDATE
    # ---------------------------------------------------
    def update_conveyor(self):
        for shape in self.shapes:
            if not shape.drag_mode:
                shape.x += shape.speed

        self.check_collisions()

        self.shapes = [s for s in self.shapes if s.x < self.width() + 150]
        self.update()

    # ---------------------------------------------------
    # HIT TEST
    # ---------------------------------------------------
    def contains(self, shape, px, py):
        return (shape.x - shape.size <= px <= shape.x + shape.size and
                shape.y - shape.size <= py <= shape.y + shape.size)

    # ---------------------------------------------------
    # LONG PRESS → GRAB MODE
    # ---------------------------------------------------
    def enable_grab(self):
        if self.active_shape:
            self.active_shape.grabbed = True
            print("[GRAB] long press → rotate mode")

    # ---------------------------------------------------
    # MOUSE PRESS
    # ---------------------------------------------------
    def mousePressEvent(self, event):
        x, y = event.x(), event.y()

        self.active_shape = None
        for s in self.shapes:
            s.selected = False

        self.last_x = x
        self.last_y = y

        for shape in reversed(self.shapes):
            if self.contains(shape, x, y):
                shape.selected = True
                self.active_shape = shape

                shape.last_press_times.append(time.time())
                shape.last_press_times = shape.last_press_times[-3:]

                # Triple tap delete
                if (len(shape.last_press_times) == 3 and
                        shape.last_press_times[-1] - shape.last_press_times[0] <= 4):
                    print("[DELETE] triple tap detected")
                    self.shapes.remove(shape)
                    return

                self.long_press_timer.start(600)
                print(f"[SELECT] {shape.shape_type} at {shape.x},{shape.y}")
                return

        self.update()

    # ---------------------------------------------------
    # MOUSE MOVE
    # ---------------------------------------------------
    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        if not self.active_shape:
            return

        x = event.x()
        y = event.y()

        dx = x - self.last_x
        dy = y - self.last_y

        self.last_x = x
        self.last_y = y

        shape = self.active_shape

        # DRAG MODE
        if shape.drag_mode and not shape.grabbed:
            shape.x += dx
            shape.y += dy
            print(f"[DRAG] → X={shape.x}, Y={shape.y}")
            self.update()
            return

        # ROTATE MODE
        if shape.grabbed:
            if dx > 0:
                shape.angle += 3
                print(f"[ROTATE] CW → {shape.angle}")
            elif dx < 0:
                shape.angle -= 3
                print(f"[ROTATE] CCW → {shape.angle}")
            self.update()
            return

    # ---------------------------------------------------
    # MOUSE RELEASE
    # ---------------------------------------------------
    def mouseReleaseEvent(self, event):
        if self.active_shape:
            if not self.active_shape.grabbed:
                self.active_shape.drag_mode = True
                print("[MODE] drag mode ON")
            else:
                print("[MODE] rotate mode OFF")

            self.active_shape.grabbed = False

        self.active_shape = None
        self.long_press_timer.stop()
        self.update()

    # ---------------------------------------------------
    # DRAWING
    # ---------------------------------------------------
    def paintEvent(self, event):
        painter = QPainter(self)

        # Conveyor
        painter.setBrush(QColor(60, 60, 60))
        painter.drawRect(0, self.height() // 2 + 80,
                         self.width(), 40)

        for shape in self.shapes:
            painter.save()

            painter.translate(shape.x, shape.y)
            painter.rotate(shape.angle)
            painter.setBrush(shape.color)

            if shape.shape_type == "circle":
                painter.drawEllipse(-shape.size, -shape.size,
                                    shape.size * 2, shape.size * 2)

            elif shape.shape_type == "square":
                painter.drawRect(-shape.size, -shape.size,
                                 shape.size * 2, shape.size * 2)

            elif shape.shape_type == "triangle":
                half = shape.size
                pts = QPolygon([
                    QPoint(0, -half),
                    QPoint(-half, half),
                    QPoint(half, half)
                ])
                painter.drawPolygon(pts)

            painter.restore()

            if shape.selected:
                painter.setPen(QPen(QColor(255, 0, 0), 4))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(shape.x - shape.size - 10,
                                    shape.y - shape.size - 10,
                                    shape.size * 2 + 20,
                                    shape.size * 2 + 20)
                painter.setPen(Qt.NoPen)


# ================================================
#   MAIN WINDOW
# ================================================

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Conveyor + Gestures + Collision (Jetson Nano)")
        self.resize(1000, 500)

        layout = QVBoxLayout()
        layout.addWidget(ConveyorWidget())
        self.setLayout(layout)


# ================================================
#               ENTRY POINT
# ================================================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
