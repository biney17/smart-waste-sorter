import cv2
from ultralytics import YOLO
import numpy as np
from pathlib import Path
import serial
import time
from collections import Counter

class WasteSorterAuto:
    def __init__(self, model_path="best.pt", port="COM35"):
        print("="*70)
        print("WASTE SORTING - AUTO DETECTION WITH ARDUINO")
        print("="*70)
        
        try:
            self.arduino = serial.Serial(port, 9600, timeout=1)
            time.sleep(2)
            print(f"Arduino connected on {port}")
        except Exception as e:
            print(f"Could not connect to Arduino on {port}: {e}")
            self.arduino = None

        print("\nLoading model...")
        model_path_obj = Path(model_path)
        if not model_path_obj.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        self.model = YOLO(str(model_path_obj))
        print(f"Model loaded!")
        
        self.class_names = self.model.names
        self.servo_angles = {
            0: 22,    # plastic
            1: 140    # paper
        }
        
        self.last_sent_angle = -1
        self.last_sent_time = 0
        self.no_detection_count = 0

        # Majority voting
        self.vote_buffer = []
        self.VOTE_WINDOW = 12
        self.VOTE_THRESHOLD = 8

        print(f"Classes: {self.class_names}")
        print("Servo: Plastic=22, Paper=140, Home=0")
        print(f"Voting: {self.VOTE_THRESHOLD}/{self.VOTE_WINDOW} frames to confirm")
        print("\n" + "="*70)
        print("CONTROLS: Q=quit | D=debug")
        print("="*70)

    def send_to_arduino(self, angle):
        if self.arduino and self.arduino.is_open:
            self.arduino.write(f"{angle}\n".encode())
            print(f"Sent to Arduino: {angle}")
        else:
            print(f"[SIM] Would send: {angle}")

    def run_camera(self, camera_index=0, debug=False):
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            print(f"Camera error {camera_index}")
            return
        
        print("Stabilizing camera (3 seconds)...")
        for _ in range(30):
            cap.read()
            time.sleep(0.1)
        print("Camera ready!")
        
        print("Forcing servo to HOME (0)...")
        self.send_to_arduino(0)
        self.last_sent_angle = 0
        time.sleep(1)
        
        send_delay = 2.0
        frame_count = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            h, w = frame.shape[:2]
            
            # Use high confidence — trust the model, no color tricks
            results = self.model(frame, conf=0.70, verbose=False)
            display_frame = frame.copy()

            # Detection zone: center 70% of frame
            zone_x1 = int(w * 0.15)
            zone_y1 = int(h * 0.10)
            zone_x2 = int(w * 0.85)
            zone_y2 = int(h * 0.90)
            cv2.rectangle(display_frame, (zone_x1, zone_y1), (zone_x2, zone_y2),
                          (100, 100, 255), 1)
            
            best_detection = None
            best_confidence = 0
            
            if results[0].boxes:
                for box in results[0].boxes:
                    class_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    
                    if class_id not in [0, 1]:
                        continue
                    if conf < 0.70:
                        continue
                    
                    bbox = box.xyxy[0].cpu().numpy()
                    x1, y1, x2, y2 = bbox
                    bbox_int = (int(x1), int(y1), int(x2), int(y2))

                    bw = x2 - x1
                    bh = y2 - y1
                    ratio = (bw * bh) / (h * w)

                    # Reject background (covers >80% of frame)
                    if ratio > 0.80:
                        if debug:
                            print(f"[REJECT] background size={ratio:.0%}")
                        continue

                    # Reject too small (noise <5%)
                    if ratio < 0.05:
                        if debug:
                            print(f"[REJECT] too small size={ratio:.0%}")
                        continue

                    # Object center must be inside detection zone
                    cx = (x1 + x2) / 2
                    cy = (y1 + y2) / 2
                    if not (zone_x1 < cx < zone_x2 and zone_y1 < cy < zone_y2):
                        if debug:
                            print(f"[REJECT] outside zone")
                        continue
                    
                    if conf > best_confidence:
                        best_confidence = conf
                        best_detection = {
                            'class_id': class_id,
                            'class_name': self.class_names[class_id],
                            'angle': self.servo_angles[class_id],
                            'bbox': bbox_int,
                            'conf': conf,
                            'ratio': ratio
                        }

            current_time = time.time()

            # ---- MAJORITY VOTING ----
            if best_detection:
                self.no_detection_count = 0
                self.vote_buffer.append(best_detection['class_id'])
                if debug:
                    print(f"Vote: {best_detection['class_name']} "
                          f"({best_detection['conf']:.0%}) "
                          f"size={best_detection['ratio']:.0%}")
            else:
                self.no_detection_count += 1
                if self.no_detection_count >= 3:
                    self.vote_buffer.append(-1)

            if len(self.vote_buffer) > self.VOTE_WINDOW:
                self.vote_buffer.pop(0)

            real_votes = [v for v in self.vote_buffer if v != -1]
            confirmed_class = None

            if len(real_votes) >= int(self.VOTE_WINDOW * 0.6):
                counts = Counter(real_votes)
                top_class, top_count = counts.most_common(1)[0]
                if top_count >= self.VOTE_THRESHOLD:
                    confirmed_class = top_class

            none_count = self.vote_buffer.count(-1)

            # ---- SEND COMMAND ----
            if confirmed_class is not None:
                angle = self.servo_angles[confirmed_class]
                if angle != self.last_sent_angle and (current_time - self.last_sent_time > send_delay):
                    self.send_to_arduino(angle)
                    self.last_sent_angle = angle
                    self.last_sent_time = current_time
                    self.vote_buffer.clear()
                    print(f">>> CONFIRMED: {self.class_names[confirmed_class]} -> {angle}")

            elif none_count >= int(self.VOTE_WINDOW * 0.8) and self.last_sent_angle != 0:
                self.send_to_arduino(0)
                self.last_sent_angle = 0
                self.last_sent_time = current_time
                self.vote_buffer.clear()
                if debug:
                    print("Object gone -> HOME (0)")

            # ---- DISPLAY ----
            if best_detection:
                x1, y1, x2, y2 = best_detection['bbox']
                color = (0, 255, 0) if best_detection['class_id'] == 0 else (255, 165, 0)
                cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 3)
                cv2.putText(display_frame,
                            f"{best_detection['class_name']} {best_detection['conf']:.0%}",
                            (x1, max(y1-10, 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

            votes_str = "".join(
                ("P" if v == 0 else "A" if v == 1 else ".")
                for v in self.vote_buffer
            )

            if len(real_votes) > 0 and confirmed_class is None:
                bar_color = (0, 200, 255)
            elif confirmed_class is not None:
                bar_color = (0, 255, 0)
            else:
                bar_color = (0, 0, 255)

            cv2.putText(display_frame,
                        f"F:{frame_count} Servo:{self.last_sent_angle} [{votes_str}]",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.55, bar_color, 2)
            cv2.putText(display_frame, "Q:Quit | D:Debug",
                        (w-200, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
            arduino_color = (0, 255, 0) if self.arduino else (0, 0, 255)
            cv2.putText(display_frame,
                        f"Arduino: {'Connected' if self.arduino else 'Disconnected'}",
                        (10, h-20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, arduino_color, 2)

            cv2.imshow("Waste Sorter - Press Q to quit, D for debug", display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == ord('Q'):
                if self.arduino and self.arduino.is_open:
                    self.arduino.write(b"0\n")
                    time.sleep(0.5)
                print("Goodbye!")
                break
            elif key == ord('d') or key == ord('D'):
                debug = not debug
                print(f"Debug: {'ON' if debug else 'OFF'}")
        
        cap.release()
        if self.arduino:
            self.arduino.close()
        cv2.destroyAllWindows()
        print(f"Session ended. {frame_count} frames processed.")

if __name__ == "__main__":
    sorter = WasteSorterAuto(model_path="best.pt", port="COM35")
    sorter.run_camera(camera_index=0, debug=True)