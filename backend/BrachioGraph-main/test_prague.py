import sys
from unittest.mock import MagicMock
sys.modules['pigpio'] = MagicMock()

from brachiograph import BrachioGraph
import json

print("=== Testing Prague-hatched.json ===\n")

# Load the JSON file from the images folder
with open('images/Prague-hatched.json', 'r') as f:
    lines = json.load(f)

print(f"✓ Loaded JSON successfully")
print(f"✓ Total lines: {len(lines)}")

# Calculate statistics
total_points = sum(len(line) for line in lines)
total_segments = sum(len(line) - 1 for line in lines)

print(f"✓ Total points: {total_points}")
print(f"✓ Total segments: {total_segments}")
print(f"✓ Average points per line: {total_points / len(lines):.1f}")

# Estimate drawing time
estimated_seconds = total_segments * 0.5  # ~0.5 seconds per segment
print(f"✓ Estimated plotter time: {estimated_seconds / 60:.1f} minutes")

# Find coordinate ranges
all_x = [point[0] for line in lines for point in line]
all_y = [point[1] for line in lines for point in line]

print(f"\nCoordinate ranges:")
print(f"  X: {min(all_x)} to {max(all_x)}")
print(f"  Y: {min(all_y)} to {max(all_y)}")

# Flip the Y coordinates to make it right-side up
max_y = max(all_y)
flipped_lines = []
for line in lines:
    flipped_line = [[point[0], max_y - point[1]] for point in line]
    flipped_lines.append(flipped_line)

print(f"\n✓ Flipped Y coordinates")

# Ask about visualization
print("\n" + "="*60)
response = input("Visualize with turtle graphics? (y/n): ").strip().lower()

if response == 'y':
    print("\nCreating virtual plotter...")

    bg = BrachioGraph(
        virtual=True,
        turtle=True,
        inner_arm=8,
        outer_arm=8,
        bounds=(-8, 4, 8, 13),
        wait=0,
        resolution=0.5
    )

    print("Plotting lines (this may take a moment with 538 lines)...")
    bg.plot_lines(flipped_lines)

    print("\n✓ Complete! Close the turtle window when done.")
    input("Press Enter to exit...")
else:
    print("\nSkipped visualization.")
    print("The SVG file should be at 'images/Prague-hatched.svg'")

print("\n=== Test Complete ===")