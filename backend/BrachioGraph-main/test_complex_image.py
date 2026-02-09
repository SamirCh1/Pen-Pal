import sys
from unittest.mock import MagicMock
sys.modules['pigpio'] = MagicMock()

from linedraw import vectorise, draw

print("=== Processing africa.jpg ===\n")

print("Processing with maximum detail...")
print("This will take 20-60 seconds...\n")

lines = vectorise(
    "africa.jpg",
    resolution=1024,
    draw_contours=4,
    repeat_contours=1,
    draw_hatch=8,
    repeat_hatch=1
)

print(f"\n✓ Processing complete!")
print(f"  Generated {len(lines)} lines")

segments = sum(len(line) - 1 for line in lines)
print(f"  Total segments: {segments}")
print(f"  Estimated plotter time: {segments * 0.5 / 60:.1f} minutes")

print(f"\n✓ Created africa.jpg.svg")
print("  Open this file in Safari/Chrome to see the preview!\n")

response = input("Show turtle graphics visualization? (y/n): ").strip().lower()

if response == 'y':
    print("\nOpening turtle window...")
    print("(This may take a moment with lots of lines)")
    print("Close the window when done.\n")
    try:
        draw(lines)
    except Exception as e:
        print(f"Turtle error: {e}")
        print("But the SVG file was created successfully!")
else:
    print("\nDone! Check africa.jpg.svg in your browser.")

print("\n=== Complete ===")