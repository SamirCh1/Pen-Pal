# Mock pigpio before importing
import sys
from unittest.mock import MagicMock
sys.modules['pigpio'] = MagicMock()

from brachiograph import BrachioGraph

# Create virtual plotter with SMALLER bounds that it can actually reach
bg = BrachioGraph(
    virtual=True,
    turtle=True,
    inner_arm=8,
    outer_arm=8,
    bounds=(-6, 6, 6, 12),  # Changed from (-8, 4, 8, 13)
    wait=0,
    resolution=0.5  # Faster simulation
)

print("Drawing a box...")
bg.box()

print("Drawing test pattern...")
bg.test_pattern(lines=3)

print("Complete! Close the turtle window when done.")
input("Press Enter to exit...")