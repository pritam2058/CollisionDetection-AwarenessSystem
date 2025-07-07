import numpy as np
import cv2

def draw_reverse_parking_lane(frame):
    h, w = frame.shape[:2]

    # Yellow Zone
    original_yellow_top_y = int(h * 0.6)
    original_yellow_bottom_y = int(h * 1.0) - 1
    new_yellow_height = int((original_yellow_bottom_y - original_yellow_top_y) * 0.55)
    new_yellow_top_y = original_yellow_bottom_y - new_yellow_height

    yellow_bottom_left_x = int(w * 0.25)
    yellow_bottom_right_x = int(w * 0.75)
    yellow_top_left_x = int(w * 0.4)
    yellow_top_right_x = int(w * 0.6)

    bottom_width = yellow_bottom_right_x - yellow_bottom_left_x

    slope_decrease_ratio = 0.165
    outward_movement = int(bottom_width * slope_decrease_ratio / 2)

    new_yellow_top_left_x = max(yellow_top_left_x - outward_movement, yellow_bottom_left_x)
    new_yellow_top_right_x = min(yellow_top_right_x + outward_movement, yellow_bottom_right_x)

    yellow_zone = np.array([
        (new_yellow_top_left_x, new_yellow_top_y),
        (new_yellow_top_right_x, new_yellow_top_y),
        (yellow_bottom_right_x, original_yellow_bottom_y),
        (yellow_bottom_left_x, original_yellow_bottom_y)
    ], dtype=np.int32)

    # Green Zone
    green_height = int(new_yellow_height * 0.5 * 1.4)
    green_bottom_y = new_yellow_top_y
    green_top_y = green_bottom_y - green_height

    slope_increase_factor = 2.0  # More inward movement towards center
    green_inward_movement = int(outward_movement * slope_increase_factor)

    green_bottom_left_x = new_yellow_top_left_x
    green_bottom_right_x = new_yellow_top_right_x

    green_top_left_x = green_bottom_left_x + green_inward_movement
    green_top_right_x = green_bottom_right_x - green_inward_movement

    green_zone = np.array([
        (green_top_left_x, green_top_y),
        (green_top_right_x, green_top_y),
        (green_bottom_right_x, green_bottom_y),
        (green_bottom_left_x, green_bottom_y)
    ], dtype=np.int32)

    # Red Zone (25% decrease in height)
    red_zone_height = int((h * 0.15) * 0.25 * 0.95 * 0.75)
    red_top_y = int(h * 1.0) - 1 - red_zone_height
    red_top_left = (int(w * 0.35), red_top_y)
    red_top_right = (int(w * 0.65), red_top_y)
    red_bottom_right = (int(w * 0.65), int(h * 1.0) - 1)
    red_bottom_left = (int(w * 0.35), int(h * 1.0) - 1)
    
    red_zone = np.array([
        red_top_left, red_top_right, red_bottom_right, red_bottom_left
    ], dtype=np.int32)

    # Draw overlays
    overlay = frame.copy()
    cv2.fillPoly(overlay, [green_zone], (0, 255, 0))
    cv2.fillPoly(overlay, [yellow_zone], (0, 255, 255))
    cv2.fillPoly(overlay, [red_zone], (0, 0, 255))
    cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)

    # Draw outlines
    cv2.polylines(frame, [green_zone], True, (0, 255, 0), 2)
    cv2.polylines(frame, [yellow_zone], True, (0, 255, 255), 2)
    cv2.polylines(frame, [red_zone], True, (0, 0, 255), 2)

    return {
        'full_trapezoid': green_zone,
        'green_zone': green_zone,
        'yellow_zone': yellow_zone,
        'red_zone': red_zone
    }





