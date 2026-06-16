import cv2
import numpy as np
import csv
import time

def get_templates():
    temp_img = np.zeros((100, 100), dtype=np.uint8)

    circle_img = temp_img.copy()
    cv2.circle(circle_img, (50, 50), 40, 255, -1)
    cnts, _ = cv2.findContours(circle_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    t_circle = cnts[0]

    square_img = temp_img.copy()
    cv2.rectangle(square_img, (20, 20), (80, 80), 255, -1)
    cnts, _ = cv2.findContours(square_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    t_square = cnts[0]

    tri_img = temp_img.copy()
    pts = np.array([[50, 20], [20, 80], [80, 80]])
    cv2.drawContours(tri_img, [pts], 0, 255, -1)
    cnts, _ = cv2.findContours(tri_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    t_triangle = cnts[0]

    return t_circle, t_square, t_triangle


def run_vision(coord_queue):
    cap = cv2.VideoCapture(0)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    SCREEN_W, SCREEN_H = 1480, 320
    template_circle, template_square, template_triangle = get_templates()

    cv2.namedWindow("Jetson Ultimate Vision", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Jetson Ultimate Vision", 1200, 300)

    with open('log_coordinates.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Timestamp', 'Shape', 'X_coord', 'Y_coord'])

        while True:
            ret, frame = cap.read()
            if not ret: break

            h, w, _ = frame.shape
            roi_h = int(w * (SCREEN_H / SCREEN_W))
            y1 = max(0, (h - roi_h) // 2)
            y2 = min(h, y1 + roi_h)
            roi = frame[y1:y2, 0:w]
            roi_display = cv2.resize(roi, (1480, 320))

            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

            lower_green = np.array([35, 40, 20])
            upper_green = np.array([90, 255, 255])
            mask = cv2.inRange(hsv, lower_green, upper_green)

            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3,3), np.uint8))
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area < 500: continue

                match_circle = cv2.matchShapes(cnt, template_circle, 1, 0.0)
                match_square = cv2.matchShapes(cnt, template_square, 1, 0.0)
                match_triangle = cv2.matchShapes(cnt, template_triangle, 1, 0.0)

                x_b, y_b, w_b, h_b = cv2.boundingRect(cnt)
                extent = float(area) / (w_b * h_b)
                hull = cv2.convexHull(cnt)
                solidity = float(area) / cv2.contourArea(hull) if cv2.contourArea(hull) > 0 else 0

                scores = {"Circle": match_circle, "Square": match_square, "Triangle": match_triangle}
                best_match = min(scores, key=scores.get)

                if solidity < 0.85 and area > 4000:
                    shape = "Overlap"
                elif best_match == "Square" and extent < 0.65:
                    shape = "Triangle"
                elif scores[best_match] > 0.35:
                    shape = "Unknown"
                else:
                    shape = best_match

                M = cv2.moments(cnt)
                if M["m00"] != 0:
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])

                    log_entry = f"[{shape}] X:{cX} Y:{cY}"
                    try:
                        coord_queue.put_nowait(log_entry)
                    except:
                        pass

                    scale_x, scale_y = 1480 / roi.shape[1], 320 / roi.shape[0]
                    draw_x, draw_y = int(cX * scale_x), int(cY * scale_y)

                    current_time = time.strftime("%H:%M:%S")
                    writer.writerow([current_time, shape, cX, cY])

                    color = (0, 0, 255) if shape in ["Overlap", "Unknown"] else (0, 255, 0)
                    cv2.drawContours(roi_display, [(cnt * [scale_x, scale_y]).astype(int)], 0, color, 2)

                    label = f"{shape} (X:{cX} Y:{cY})"
                    cv2.putText(roi_display, label, (draw_x - 60, draw_y - 15),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                    cv2.circle(roi_display, (draw_x, draw_y), 3, (255, 255, 255), -1)

            cv2.imshow("Jetson Ultimate Vision", roi_display)
            if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()
