from ultralytics import YOLO
import numpy as np
import cv2

# Load YOLO model
model = YOLO("yolov8n.pt")
model.to("cpu")

# Define vehicle classes (COCO IDs)
vehicle_classes = {
    2: ("car", (0, 255, 0)),
    3: ("motorcycle", (0, 255, 0)),
    5: ("bus", (0, 255, 0)),
    7: ("truck", (0, 255, 0))
}

def detect_vehicles(frame, lane_zones, filter_inside=True, min_overlap_ratio=0.05, return_class_ids=False):
    result = model(frame)[0]

    boxes = []
    class_ids = []
    zone_names = []

    for box in result.boxes:
        cls_id = int(box.cls[0])
        if cls_id not in vehicle_classes:
            continue

        x1, y1, x2, y2 = map(int, box.xyxy[0])
        box_polygon = np.array([[x1, y1], [x2, y1], [x2, y2], [x1, y2]], dtype=np.int32)
        bbox_area = (x2 - x1) * (y2 - y1)

        # Optional: Check if vehicle is inside full trapezoid
        if filter_inside:
            intersection_area, _ = cv2.intersectConvexConvex(
                box_polygon.astype(np.float32),
                lane_zones['full_trapezoid'].astype(np.float32)
            )
            overlap_ratio = intersection_area / bbox_area if bbox_area > 0 else 0
            if overlap_ratio < min_overlap_ratio:
                continue

        # Identify which lane zone the box overlaps with
        detected_zone = None
        for zone_name in ['red_zone', 'yellow_zone', 'green_zone']:
            zone_polygon = lane_zones[zone_name]
            intersection_area, _ = cv2.intersectConvexConvex(
                box_polygon.astype(np.float32),
                zone_polygon.astype(np.float32)
            )
            overlap_ratio = intersection_area / bbox_area if bbox_area > 0 else 0
            if overlap_ratio >= min_overlap_ratio:
                detected_zone = zone_name
                break

        if detected_zone is None:
            continue

        # Collect detection results
        boxes.append((x1, y1, x2, y2))
        class_ids.append(cls_id)
        zone_names.append(detected_zone)

    # Return original frame (no drawings) + detection results
    if return_class_ids:
        return frame.copy(), boxes, class_ids, zone_names
    else:
        return frame.copy(), boxes





