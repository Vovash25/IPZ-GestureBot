import sys
import random
import time
import math
import threading
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QHBoxLayout
from PyQt5.QtGui import QPainter, QColor, QPolygon, QPen, QImage, QPixmap
from PyQt5.QtCore import Qt, QPoint, QTimer, pyqtSignal, QObject

import cv2
import mediapipe as mp

import os
os.environ['MEDIAPIPE_RESOURCES_PATH'] = '/usr/local/lib/python3.6/dist-packages/mediapipe'

class AIController(QObject):
    """Klasa do kontroli AI za pomocą kamery dla MediaPipe 0.8.5"""
    update_position = pyqtSignal(int, int, str)  # x, y, gesture_type

    def __init__(self):
        super().__init__()
        self.running = False
        self.cap = None
        self.mp_hands = None
        self.hands = None
        self.mp_drawing = None

        # Wymiary ekranu
        self.screen_width = 1000
        self.screen_height = 500

    def start_camera(self):
        """Uruchamia kamerę dla MediaPipe 0.8.5"""

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Cannot open camera")
            return

        try:
            # Inicjalizacja MediaPipe 0.8.5
            self.mp_drawing = mp.solutions.drawing_utils
            self.mp_hands = mp.solutions.hands

            # Ustawienie parametrów ręcznie, aby uniknąć błędów ładowania modeli
            self.hands = self.mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=1,
                min_detection_confidence=0.7,
                min_tracking_confidence=0.5

            )

            self.running = True
            print("AI Camera started (MediaPipe 0.8.5)")

            # Wątek przetwarzania
            self.thread = threading.Thread(target=self.process_camera_0_8_5)
            self.thread.daemon = True
            self.thread.start()

        except Exception as e:
            print(f"Error starting camera: {e}")
            self.running = False
            if self.cap:
                self.cap.release()

    def stop_camera(self):
        """Zatrzymuje kamerę"""
        self.running = False
        if self.cap:
            self.cap.release()
        if self.hands:
            self.hands.close()
        cv2.destroyAllWindows()
        print("AI Camera stopped")

    def process_camera_0_8_5(self):
        """Główna pętla przetwarzania dla MediaPipe 0.8.5"""
        while self.running and self.cap and self.cap.isOpened():
            try:
                ret, frame = self.cap.read()
                if not ret:
                    time.sleep(0.01)
                    continue

                # Odwróć obraz
                frame = cv2.flip(frame, 1)
                h, w, _ = frame.shape

                # Konwersja do RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Przetwarzanie przez MediaPipe
                results = self.hands.process(rgb_frame)

                if results.multi_hand_landmarks:
                    # Weź pierwszą wykrytą dłoń
                    hand_landmarks = results.multi_hand_landmarks[0]

                    # Narysuj punkty
                    self.mp_drawing.draw_landmarks(
                        frame,
                        hand_landmarks,
                        self.mp_hands.HAND_CONNECTIONS,
                        self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                        self.mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2)
                    )

                    # Oblicz środek dłoni
                    landmarks = hand_landmarks.landmark

                    # Użyj punktu nadgarstka (punkt 0) lub oblicz środek
                    wrist = landmarks[0]  # WRIST

                    # Konwertuj do współrzędnych ekranu
                    screen_x = int(wrist.x * self.screen_width)
                    screen_y = int(wrist.y * self.screen_height)

                    # Ogranicz do granic ekranu
                    screen_x = max(0, min(screen_x, self.screen_width - 1))
                    screen_y = max(0, min(screen_y, self.screen_height - 1))

                    # Detekcja gestu
                    gesture = self.simple_gesture_detection(landmarks)

                    # Wyślij pozycję
                    self.update_position.emit(screen_x, screen_y, gesture)

                    # Dodaj informację na podglądzie
                    cv2.putText(frame, f"Gesture: {gesture}", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    cv2.putText(frame, f"Pos: ({screen_x}, {screen_y})", (10, 60),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                # Wyświetl podgląd
                cv2.imshow('AI Controller Preview', frame)

                # Sprawdź czy użytkownik chce wyjść
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:  # 'q' lub ESC
                    break

            except Exception as e:
                print(f"Camera processing error: {e}")
                time.sleep(0.1)
                continue

        cv2.destroyAllWindows()

    def simple_gesture_detection(self, landmarks):
        """Prosta detekcja gestów dla MediaPipe 0.8.5"""
        try:
            # Indeksy punktów dla MediaPipe 0.8.5
            # THUMB_TIP = 4, INDEX_FINGER_TIP = 8, MIDDLE_FINGER_TIP = 12
            thumb_tip = landmarks[4]
            index_tip = landmarks[8]
            middle_tip = landmarks[12]

            # Oblicz odległość między kciukiem a wskazującym
            thumb_index_dist = math.sqrt(
                (thumb_tip.x - index_tip.x) ** 2 +
                (thumb_tip.y - index_tip.y) ** 2
            )

            # Sprawdź czy środkowy palec jest wyżej niż wskazujący (gest "peace")
            middle_higher = middle_tip.y < index_tip.y

            if thumb_index_dist < 0.05:  # Kciuk blisko wskazującego
                return "grab"
            elif middle_higher:  # Środkowy palec wyżej
                return "rotate"
            else:  # Dłoń otwarta
                return "move"

        except:
            return "move"

    def set_screen_size(self, width, height):
        """Ustawia rozmiar ekranu"""
        self.screen_width = width
        self.screen_height = height


# Pozostała część kodu bez zmian (Shape, ConveyorWidget, MainWindow klas)
class Shape:
    def __init__(self, x, y, size, color, shape_type, angle, speed):
        self.x = x
        self.y = y
        self.size = size
        self.color = color
        self.shape_type = shape_type
        self.angle = angle
        self.speed = speed

        self.selected = False
        self.grabbed = False
        self.drag_mode = False
        self.last_press_times = []
        self.ai_controlled = False


class ConveyorWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.shapes = []
        self.active_shape = None
        self.ai_active = False
        self.ai_target_shape = None

        self.last_x = None
        self.last_y = None

        # Inicjalizacja kontrolera AI
        self.ai_controller = AIController()
        self.ai_controller.update_position.connect(self.on_ai_update)

        # Timery
        self.long_press_timer = QTimer()
        self.long_press_timer.setSingleShot(True)
        self.long_press_timer.timeout.connect(self.enable_grab)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_conveyor)
        self.timer.start(30)

        # Inicjalizuj figury
        self.init_shapes()

    def init_shapes(self):
        """Inicjalizuje kilka statycznych figur na ekranie"""
        shapes_data = [
            {"x": 200, "y": 200, "size": 40, "type": "circle", "angle": 0},
            {"x": 400, "y": 300, "size": 50, "type": "square", "angle": 45},
            {"x": 600, "y": 150, "size": 35, "type": "triangle", "angle": 90},
            {"x": 300, "y": 400, "size": 45, "type": "circle", "angle": 30},
            {"x": 700, "y": 250, "size": 55, "type": "triangle", "angle": 120},
        ]

        for data in shapes_data:
            shape = Shape(
                x=data["x"],
                y=data["y"],
                size=data["size"],
                color=QColor(random.randint(50, 250),
                             random.randint(50, 250),
                             random.randint(50, 250)),
                shape_type=data["type"],
                angle=data["angle"],
                speed=0
            )
            self.shapes.append(shape)
        print(f"[INIT] Created {len(self.shapes)} static shapes")

    def toggle_ai_control(self):
        """Włącza/wyłącza kontrolę AI"""
        self.ai_active = not self.ai_active

        if self.ai_active:
            # Przekaż rozmiar widgetu do kontrolera AI
            self.ai_controller.set_screen_size(self.width(), self.height())
            self.ai_controller.start_camera()
            print("AI control ENABLED")

            # Wybierz pierwszą figurę do kontroli AI
            if self.shapes:
                self.ai_target_shape = self.shapes[0]
                self.ai_target_shape.ai_controlled = True
                self.ai_target_shape.color = QColor(0, 255, 0)  # Zielony dla AI
                print(f"AI controlling: {self.ai_target_shape.shape_type}")
        else:
            self.ai_controller.stop_camera()
            if self.ai_target_shape:
                self.ai_target_shape.ai_controlled = False
                self.ai_target_shape.color = QColor(random.randint(50, 250),
                                                    random.randint(50, 250),
                                                    random.randint(50, 250))
                self.ai_target_shape = None
            print("AI control DISABLED")

        self.update()

    def on_ai_update(self, x, y, gesture):
        """Obsługa aktualizacji pozycji od AI"""
        if not self.ai_active or not self.ai_target_shape:
            return

        # Aktualizuj pozycję figury
        self.ai_target_shape.x = x
        self.ai_target_shape.y = y

        # Ogranicz do granic ekranu
        self.ai_target_shape.x = max(self.ai_target_shape.size,
                                     min(self.ai_target_shape.x,
                                         self.width() - self.ai_target_shape.size))
        self.ai_target_shape.y = max(self.ai_target_shape.size,
                                     min(self.ai_target_shape.y,
                                         self.height() - self.ai_target_shape.size))

        # Obsługa gestów
        if gesture == "grab":
            self.ai_target_shape.color = QColor(255, 0, 0)  # Czerwony
            self.ai_target_shape.size = min(80, self.ai_target_shape.size + 2)
        elif gesture == "rotate":
            self.ai_target_shape.angle += 10
            if self.ai_target_shape.angle > 360:
                self.ai_target_shape.angle = 0
            self.ai_target_shape.color = QColor(0, 0, 255)  # Niebieski
        elif gesture == "move":
            self.ai_target_shape.color = QColor(0, 255, 0)  # Zielony
            self.ai_target_shape.size = max(20, self.ai_target_shape.size - 1)

        self.update()

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

    def update_conveyor(self):
        self.check_collisions()
        self.update()

    def contains(self, shape, px, py):
        return (shape.x - shape.size <= px <= shape.x + shape.size and
                shape.y - shape.size <= py <= shape.y + shape.size)

    def enable_grab(self):
        if self.active_shape:
            self.active_shape.grabbed = True
            print("[GRAB] long press → rotate mode")

    def mousePressEvent(self, event):
        # Jeśli AI jest aktywne, wyłącz myszkę dla wybranej figury
        if self.ai_active and self.ai_target_shape:
            return

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

                if (len(shape.last_press_times) == 3 and
                        shape.last_press_times[-1] - shape.last_press_times[0] <= 0.4):
                    print("[DELETE] triple tap detected")
                    self.shapes.remove(shape)
                    return

                self.long_press_timer.start(600)
                print(f"[SELECT] {shape.shape_type} at {round(shape.x, 2)},{round(shape.y, 2)}")
                return

        self.update()

    def mouseMoveEvent(self, event):
        if self.ai_active and self.ai_target_shape:
            return

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

        if shape.drag_mode and not shape.grabbed:
            shape.x += dx
            shape.y += dy
            print(f"[DRAG] → X={round(shape.x, 2)}, Y={round(shape.y, 2)}")
            self.update()
            return

        if shape.grabbed:
            if dx > 0:
                shape.angle += 3
                print(f"[ROTATE] CW → {shape.angle}")
            elif dx < 0:
                shape.angle -= 3
                print(f"[ROTATE] CCW → {shape.angle}")
            self.update()
            return

    def mouseReleaseEvent(self, event):
        if self.ai_active and self.ai_target_shape:
            return

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

    def paintEvent(self, event):
        painter = QPainter(self)

        # Tło
        painter.fillRect(self.rect(), QColor(40, 40, 40))

        # Pasek konwejora
        painter.setBrush(QColor(60, 60, 60))
        painter.drawRect(0, self.height() // 2 + 80,
                         self.width(), 40)

        # Rysuj figury
        for shape in self.shapes:
            painter.save()

            # Obwódka dla AI
            if shape.ai_controlled:
                painter.setPen(QPen(QColor(0, 255, 0), 3))
            elif shape.selected:
                painter.setPen(QPen(QColor(255, 0, 0), 3))
            else:
                painter.setPen(Qt.NoPen)

            painter.translate(int(shape.x), int(shape.y))
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

        # Informacja o AI
        if self.ai_active:
            painter.setPen(QColor(0, 255, 0))
            painter.setFont(self.font())
            painter.drawText(10, 20, "AI CONTROL: ACTIVE (Use hand gestures)")
            if self.ai_target_shape:
                painter.drawText(10, 40, f"Controlling: {self.ai_target_shape.shape_type}")
                painter.drawText(10, 60, f"Position: ({int(self.ai_target_shape.x)}, {int(self.ai_target_shape.y)})")
        else:
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(10, 20, "AI CONTROL: DISABLED")


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Shape Controller with Camera (MediaPipe 0.8.5)")
        self.resize(1000, 600)  # Nieco większe okno

        # Główny widget
        self.conveyor = ConveyorWidget()

        # Przyciski kontroli
        self.btn_ai_toggle = QPushButton("Start AI Control")
        self.btn_ai_toggle.clicked.connect(self.toggle_ai)
        self.btn_ai_toggle.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

        self.btn_add_shape = QPushButton("Add Random Shape")
        self.btn_add_shape.clicked.connect(self.add_shape)

        self.btn_clear = QPushButton("Clear All")
        self.btn_clear.clicked.connect(self.clear_shapes)
        self.btn_clear.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)

        # Layout przycisków
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.btn_ai_toggle)
        button_layout.addWidget(self.btn_add_shape)
        button_layout.addWidget(self.btn_clear)

        # Główny layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.conveyor)

        self.setLayout(main_layout)

    def toggle_ai(self):
        self.conveyor.toggle_ai_control()
        if self.conveyor.ai_active:
            self.btn_ai_toggle.setText("Stop AI Control")
            self.btn_ai_toggle.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    font-weight: bold;
                    padding: 10px;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #d32f2f;
                }
            """)
        else:
            self.btn_ai_toggle.setText("Start AI Control")
            self.btn_ai_toggle.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    font-weight: bold;
                    padding: 10px;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)

    def add_shape(self):
        """Dodaje nową figurę"""
        shape_types = ["circle", "square", "triangle"]
        shape = Shape(
            x=random.randint(100, 900),
            y=random.randint(100, 400),
            size=random.randint(30, 60),
            color=QColor(random.randint(50, 250),
                         random.randint(50, 250),
                         random.randint(50, 250)),
            shape_type=random.choice(shape_types),
            angle=random.randint(0, 360),
            speed=0
        )
        self.conveyor.shapes.append(shape)
        print(f"[ADD] New {shape.shape_type} at {shape.x},{shape.y}")

    def clear_shapes(self):
        """Czyści wszystkie figury"""
        self.conveyor.shapes.clear()
        print("[CLEAR] All shapes removed")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
