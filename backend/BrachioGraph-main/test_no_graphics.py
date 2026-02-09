import sys
from unittest.mock import MagicMock
sys.modules['pigpio'] = MagicMock()

from brachiograph import BrachioGraph
import json

# Create virtual plotter WITHOUT turtle
bg = BrachioGraph(
    virtual=True,
    turtle=False,  # No graphics window
    inner_arm=8,
    outer_arm=8,
    bounds=(-6, 6, 6, 12),
    wait=0,
    resolution=0.5
)

print("\n=== Testing Virtual Plotter ===\n")

print("Drawing a box...")
bg.box()

print("\nDrawing vertical lines...")
bg.vertical_lines(lines=5)

print("\nTesting coordinate conversion:")
test_points = [(0, 10), (2, 12), (-2, 12)]
for x, y in test_points:
    try:
        angles = bg.xy_to_angles(x, y)
        print(f"  ({x:>3}, {y:>2}) -> shoulder: {angles[0]:>6.1f}°, elbow: {angles[1]:>6.1f}°")
    except:
        print(f"  ({x:>3}, {y:>2}) -> OUT OF REACH")

print("\n=== Test Complete ===")
bg.park()