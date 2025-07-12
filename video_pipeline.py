import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import threading
import cv2
import queue
import time
import pygame
import numpy as np

from vehicle_detection import detect_vehicles, vehicle_classes
from vehicle_tracking import VehicleTracker
from speed_estimation import SpeedEstimator  # Use your updated SpeedEstimator with homography
from lane_detection import draw_reverse_parking_lane

class VideoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Collision Detection and Awareness System")
        self.root.geometry("800x600")

        self.video_path = None
        self.cap = None
        self.playing = False
        self.paused = False

        self.frame_width = 760
        self.frame_height = 480

        self.frame_queue = queue.Queue(maxsize=5)
        self.output_queue = queue.Queue(maxsize=5)

        self.display_frame = tk.Frame(root, width=self.frame_width, height=self.frame_height, bg="black", bd=2, relief=tk.SOLID)
        self.display_frame.pack(pady=10)
        self.display_frame.pack_propagate(0)

        self.display_label = tk.Label(self.display_frame, bg="black", fg="white", text="No video selected", font=("Arial", 16))
        self.display_label.pack(expand=True, fill=tk.BOTH)

        self.lights_frame = tk.Frame(root)
        self.lights_frame.pack(side=tk.TOP, pady=10)

        self.green_light = tk.Canvas(self.lights_frame, width=30, height=30, bg='black', highlightthickness=0)
        self.green_light.create_oval(2, 2, 28, 28, fill='green', tags='light')
        self.green_light.pack(side=tk.LEFT, padx=5)

        self.yellow_light = tk.Canvas(self.lights_frame, width=30, height=30, bg='black', highlightthickness=0)
        self.yellow_light.create_oval(2, 2, 28, 28, fill='grey', tags='light')
        self.yellow_light.pack(side=tk.LEFT, padx=5)

        self.red_light = tk.Canvas(self.lights_frame, width=30, height=30, bg='black', highlightthickness=0)
        self.red_light.create_oval(2, 2, 28, 28, fill='grey', tags='light')
        self.red_light.pack(side=tk.LEFT, padx=5)

        self.bottom_frame = tk.Frame(root)
        self.bottom_frame.pack(side=tk.BOTTOM, anchor='w', padx=10, pady=10)

        self.btn_choose = tk.Button(self.bottom_frame, text="Choose Video", command=self.choose_video)
        self.btn_choose.pack(side=tk.LEFT, padx=5)

        self.btn_play = tk.Button(self.bottom_frame, text="Play", command=self.play_video, state=tk.DISABLED)
        self.btn_play.pack(side=tk.LEFT, padx=5)

        self.btn_pause_resume = tk.Button(self.bottom_frame, text="Pause", command=self.pause_resume_video, state=tk.DISABLED)
        self.btn_pause_resume.pack(side=tk.LEFT, padx=5)

        self.stop_event = threading.Event()

        self.tracker = VehicleTracker()
        self.speed_estimator = SpeedEstimator(fps=30)  # use homography-based speed estimator

        pygame.mixer.init()
        self.alert_yellow = pygame.mixer.Sound("alert_audio/yellow_zone.mp3")
        self.alert_red = pygame.mixer.Sound("alert_audio/red_zone.mp3")

        self.current_alert = None

    def update_lights(self, status):
        if status == 'red':
            self.red_light.itemconfig('light', fill='red')
            self.yellow_light.itemconfig('light', fill='grey')
            self.green_light.itemconfig('light', fill='grey')
        elif status == 'yellow':
            self.red_light.itemconfig('light', fill='grey')
            self.yellow_light.itemconfig('light', fill='yellow')
            self.green_light.itemconfig('light', fill='grey')
        else:
            self.red_light.itemconfig('light', fill='grey')
            self.yellow_light.itemconfig('light', fill='grey')
            self.green_light.itemconfig('light', fill='green')

    def play_alert(self, status):
        if status == 'red':
            if self.current_alert != 'red':
                pygame.mixer.stop()
                self.alert_red.play(loops=-1)
                self.current_alert = 'red'
        elif status == 'yellow':
            if self.current_alert != 'yellow':
                pygame.mixer.stop()
                self.alert_yellow.play(loops=-1)
                self.current_alert = 'yellow'
        elif status == 'green':
            if self.current_alert != 'green':
                pygame.mixer.stop()
                self.current_alert = 'green'

    def stop_video(self):
        if self.playing:
            self.stop_event.set()
            self.playing = False
            self.paused = False
            if self.cap:
                self.cap.release()
                self.cap = None
            with self.frame_queue.mutex:
                self.frame_queue.queue.clear()
            with self.output_queue.mutex:
                self.output_queue.queue.clear()
            self.display_label.config(image='', text="No video selected")
            self.btn_play.config(state=tk.NORMAL)
            self.btn_pause_resume.config(state=tk.DISABLED)
            self.btn_pause_resume.config(text="Pause")
            self.update_lights('green')
            self.play_alert('green')

    def choose_video(self):
        self.stop_video()
        file_path = filedialog.askopenfilename(
            title="Select video file",
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv"), ("All files", "*.*")]
        )
        if file_path:
            self.video_path = file_path
            self.btn_play.config(state=tk.NORMAL)
            self.display_label.config(text="")

    def play_video(self):
        if not self.video_path:
            return

        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Cannot open video file.")
            return

        self.playing = True
        self.paused = False
        self.stop_event.clear()
        self.btn_play.config(state=tk.DISABLED)
        self.btn_pause_resume.config(state=tk.NORMAL)
        self.btn_pause_resume.config(text="Pause")

        self.tracker = VehicleTracker()
        self.speed_estimator = SpeedEstimator(fps=30)

        with self.frame_queue.mutex:
            self.frame_queue.queue.clear()
        with self.output_queue.mutex:
            self.output_queue.queue.clear()

        threading.Thread(target=self.read_frames, daemon=True).start()
        threading.Thread(target=self.process_frames, daemon=True).start()
        self.update_frame_ui()

    def pause_resume_video(self):
        if self.playing:
            self.paused = not self.paused
            self.btn_pause_resume.config(text="Resume" if self.paused else "Pause")

            if self.paused:
                # Pause all sounds
                pygame.mixer.pause()
            else:
                # Resume all sounds
                pygame.mixer.unpause()

    def read_frames(self):
        while not self.stop_event.is_set():
            if self.paused:
                time.sleep(0.1)
                continue

            ret, frame = self.cap.read()
            if not ret:
                self.stop_event.set()
                break
            try:
                self.frame_queue.put(frame, timeout=1)
            except queue.Full:
                pass
            time.sleep(0.01)

        if self.cap:
            self.cap.release()
            self.cap = None

    def process_frames(self):
        def get_zone_for_box(box, lane_zones, min_overlap_ratio=0.05):
            x1, y1, x2, y2 = box
            box_polygon = np.array([[x1, y1], [x2, y1], [x2, y2], [x1, y2]], dtype=np.int32)
            bbox_area = (x2 - x1) * (y2 - y1)

            for zone_name in ['red_zone', 'yellow_zone', 'green_zone']:
                zone_polygon = lane_zones[zone_name]
                intersection_area, _ = cv2.intersectConvexConvex(
                    box_polygon.astype(np.float32),
                    zone_polygon.astype(np.float32)
                )
                overlap_ratio = intersection_area / bbox_area if bbox_area > 0 else 0
                if overlap_ratio >= min_overlap_ratio:
                    return zone_name
            return None

        while not self.stop_event.is_set() or not self.frame_queue.empty():
            if self.paused:
                time.sleep(0.1)
                continue

            try:
                frame = self.frame_queue.get(timeout=1)
            except queue.Empty:
                continue

            frame = cv2.resize(frame, (self.frame_width, self.frame_height))
            lane_zones = draw_reverse_parking_lane(frame)


            annotated_frame, boxes, class_ids, zone_names = detect_vehicles(frame, lane_zones, return_class_ids=True)
            tracks = self.tracker.update_tracks(boxes, frame)

            has_red = False
            has_yellow = False

            for ((track_id, x1, y1, x2, y2), cls_id, zone_name) in zip(tracks, class_ids, zone_names):
                vehicle_name, base_color = vehicle_classes.get(cls_id, ("vehicle", (0, 255, 0)))

                self.speed_estimator.update(track_id, x1, y1, x2, y2)
                speed = self.speed_estimator.compute_speed(track_id)

                bbox_color = base_color

                if zone_name == "green_zone":
                    if speed is None or speed <= 10:
                        bbox_color = (0, 255, 0)
                    else:
                        bbox_color = (0, 255, 255)
                        has_yellow = True
                elif zone_name == "yellow_zone":
                    if speed is None or speed <= 8:
                        bbox_color = (0, 255, 255)
                        has_yellow = True
                    else:
                        bbox_color = (0, 0, 255)
                        has_red = True
                elif zone_name == "red_zone":
                    if speed is None or speed <= 5:
                        bbox_color = (0, 255, 255)
                        has_yellow = True
                    else:
                        bbox_color = (0, 0, 255)
                        has_red = True

                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), bbox_color, 2)
                cv2.putText(annotated_frame, vehicle_name, (x1, y1 - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, bbox_color, 2)
                display_speed = f"{speed:.3f} km/h" if speed is not None else "Calculating"
                cv2.putText(annotated_frame, f"Speed: {display_speed}", (x1, y2 + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                            bbox_color, 2)

            # Update traffic lights and alerts
            if has_red:
                self.update_lights('red')
                traffic_status = 'red'
            elif has_yellow:
                self.update_lights('yellow')
                traffic_status = 'yellow'
            else:
                self.update_lights('green')
                traffic_status = 'green'

            self.play_alert(traffic_status)

            self.speed_estimator.next_frame()

            try:
                self.output_queue.put(annotated_frame, timeout=1)
            except queue.Full:
                pass

    def update_frame_ui(self):
        if not self.playing and self.output_queue.empty():
            self.btn_play.config(state=tk.NORMAL)
            self.btn_pause_resume.config(state=tk.DISABLED)
            self.display_label.config(text="No video selected")
            return

        try:
            frame = self.output_queue.get_nowait()
        except queue.Empty:
            frame = None

        if frame is not None:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)
            self.display_label.imgtk = imgtk
            self.display_label.config(image=imgtk)

        self.root.after(30, self.update_frame_ui)


def start_app():
    root = tk.Tk()
    app = VideoApp(root)
    root.mainloop()
