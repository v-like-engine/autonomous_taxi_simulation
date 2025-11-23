"""
Diagnostic tool to check HSV color ranges in test maps.
"""

import sys
import os
import cv2
import numpy as np

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def analyze_colors(image, label, x, y, w, h):
    """Analyze colors in a region."""
    region = image[y:y+h, x:x+w]

    # Convert to HSV
    hsv_region = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)

    # Get statistics
    mean_bgr = np.mean(region.reshape(-1, 3), axis=0)
    mean_hsv = np.mean(hsv_region.reshape(-1, 3), axis=0)

    min_hsv = np.min(hsv_region.reshape(-1, 3), axis=0)
    max_hsv = np.max(hsv_region.reshape(-1, 3), axis=0)

    print(f"\n{label}:")
    print(f"  BGR: [{int(mean_bgr[0])}, {int(mean_bgr[1])}, {int(mean_bgr[2])}]")
    print(f"  HSV mean: [{int(mean_hsv[0])}, {int(mean_hsv[1])}, {int(mean_hsv[2])}]")
    print(f"  HSV min: [{int(min_hsv[0])}, {int(min_hsv[1])}, {int(min_hsv[2])}]")
    print(f"  HSV max: [{int(max_hsv[0])}, {int(max_hsv[1])}, {int(max_hsv[2])}]")


def create_test_map_for_analysis():
    """Create test map with known color regions."""
    width, height = 800, 600
    image = np.ones((height, width, 3), dtype=np.uint8) * 242

    # Yellow road (Google Maps style)
    cv2.rectangle(image, (350, 0), (380, 600), (80, 200, 250), -1)

    # Green park
    cv2.rectangle(image, (50, 50), (200, 200), (180, 230, 180), -1)

    # Blue water
    cv2.circle(image, (650, 150), 80, (220, 180, 130), -1)

    # White road
    cv2.rectangle(image, (150, 250), (157, 350), (255, 255, 255), -1)

    # Gray road
    cv2.rectangle(image, (500, 150), (507, 250), (200, 200, 200), -1)

    return image


if __name__ == '__main__':
    print("=" * 70)
    print("COLOR ANALYSIS FOR MAP PARSING")
    print("=" * 70)

    # Create test map
    test_image = create_test_map_for_analysis()
    cv2.imwrite('/home/user/autonomous_taxi_simulation/color_test_map.png', test_image)

    # Analyze different regions
    analyze_colors(test_image, "Yellow Main Road", 350, 300, 30, 30)
    analyze_colors(test_image, "Green Park", 100, 100, 50, 50)
    analyze_colors(test_image, "Blue Water", 630, 130, 40, 40)
    analyze_colors(test_image, "White Road", 150, 270, 7, 30)
    analyze_colors(test_image, "Gray Road", 500, 180, 7, 30)
    analyze_colors(test_image, "Background", 400, 100, 30, 30)

    print("\n" + "=" * 70)
    print("Color ranges to use in HSV:")
    print("=" * 70)

    print("\nYellow roads: lower=[15-25, 150-200, 200-255], upper=[30-35, 255, 255]")
    print("Green parks: lower=[35-45, 50-100, 150-200], upper=[75-85, 255, 255]")
    print("Blue water: lower=[85-95, 50-100, 100-150], upper=[110-120, 255, 255]")
    print("White roads: lower=[0, 0, 200-240], upper=[180, 30-50, 255]")
    print("Gray roads: lower=[0, 0, 150-200], upper=[180, 30-50, 220-240]")

    print("\nNote: These ranges should be adjusted based on actual map images.")
