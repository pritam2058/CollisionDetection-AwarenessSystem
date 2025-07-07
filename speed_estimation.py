from collections import defaultdict


class SpeedEstimator:
    def __init__(self, pixels_per_meter=8, fps=30, my_speed_km_ph=30):
        self.pixels_per_meter = pixels_per_meter
        self.fps = fps
        self.my_speed_km_ph = my_speed_km_ph
        self.track_history = defaultdict(list)
        self.frame_index = 0

    def update(self, track_id, y1, y2):
        center_y = (y1 + y2) / 2
        self.track_history[track_id].append((self.frame_index, center_y))

    def compute_speed(self, track_id):
        history = self.track_history[track_id]
        if len(history) < 2:
            return None
        f1, y1 = history[0]
        f2, y2 = history[-1]
        time_elapsed = (f2 - f1) / self.fps
        if time_elapsed <= 0:
            return None
        displacement = (y2 - y1) / self.pixels_per_meter
        speed_mps = displacement / time_elapsed
        speed_kmph = speed_mps * 3.6 + self.my_speed_km_ph
        return round(speed_kmph, 2)

    def next_frame(self):
        self.frame_index += 1

