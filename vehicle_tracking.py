from deep_sort_realtime.deepsort_tracker import DeepSort
import cv2

class VehicleTracker:
    def __init__(self):
        self.tracker = DeepSort(max_age=30)

    def update_tracks(self, boxes, frame, lane_polygon=None):
        detections = []
        for x1, y1, x2, y2 in boxes:
            w, h = x2 - x1, y2 - y1
            center = ((x1 + x2) // 2, (y1 + y2) // 2)

            if lane_polygon is not None and cv2.pointPolygonTest(lane_polygon, center, False) < 0:
                continue

            detections.append(([x1, y1, w, h], 0.9, "vehicle"))

        results = []
        tracks = self.tracker.update_tracks(detections, frame=frame)
        for track in tracks:
            if not track.is_confirmed():
                continue

            track_id = track.track_id
            x1, y1, x2, y2 = map(int, track.to_ltrb())
            center = ((x1 + x2) // 2, (y1 + y2) // 2)

            if lane_polygon is not None and cv2.pointPolygonTest(lane_polygon, center, False) < 0:
                continue

            results.append((track_id, x1, y1, x2, y2))

        return results

