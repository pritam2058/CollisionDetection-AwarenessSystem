
import numpy as np
from collections import defaultdict
import cv2

class SpeedEstimator:
    def __init__(self, fps=30):
        self.fps = fps
        self.track_history = defaultdict(list)  # track_id: list of (frame_idx, x_m, y_m)
        self.frame_index = 0

        # Image frame size (adjust as per your project)
        self.frame_width = 760
        self.frame_height = 480

        # Define lane trapezoid pixel points (source points)
        # top_y = 150
        # bottom_y = top_y + 177

        # self.src_points = np.float32([
        #     [self.frame_width * 0.3, top_y],  # Top-left
        #     [self.frame_width * 0.7, top_y],  # Top-right
        #     [self.frame_width * 0.7, bottom_y],  # Bottom-right
        #     [self.frame_width * 0.3, bottom_y]  # Bottom-left
        # ])

        self.src_points = np.float32([
            [228, 302],
            [532, 302],
            [532, 479],
            [228, 479]
        ])

        # Corresponding real-world points in meters (destination points)
        self.dst_points = np.float32([
            [0, 0],  # Top-left (meters)
            [1.77, 0],  # Top-right (meters) — matches bottom width of 1.77m
            [1.77, 0.825],  # Bottom-right (meters) — corrected total height
            [0, 0.825]  # Bottom-left (meters)
        ])

        # Compute homography matrix from pixels to real-world meters
        self.M = cv2.getPerspectiveTransform(self.src_points, self.dst_points)

    def update(self, track_id, x1, y1, x2, y2):
        """
        Update track history with real-world coordinates transformed from bbox bottom-center pixel.
        """
        x_center = (x1 + x2) / 2
        y_bottom = y2

        # Pixel point as input for homography transform (shape must be (1,1,2))
        pixel_point = np.array([[[x_center, y_bottom]]], dtype=np.float32)
        real_world_point = cv2.perspectiveTransform(pixel_point, self.M)
        x_m, y_m = real_world_point[0][0]

        self.track_history[track_id].append((self.frame_index, x_m, y_m))

    def compute_speed(self, track_id):
        history = self.track_history[track_id]
        if len(history) < 2:
            return None

        f1, x1, y1 = history[0]
        f2, x2, y2 = history[-1]

        time_elapsed = (f2 - f1) / self.fps
        if time_elapsed <= 0:
            return None

        dist_m = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        speed_mps = dist_m / time_elapsed
        speed_kmph = speed_mps * 3.6  # meters per second to km/h

        return round(speed_kmph, 3)

    def next_frame(self):
        self.frame_index += 1
