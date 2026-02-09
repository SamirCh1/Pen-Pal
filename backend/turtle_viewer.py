#!/usr/bin/env python3
import sys
from unittest.mock import MagicMock
sys.modules['pigpio'] = MagicMock()

import json
import os

# Add brachiograph-main to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'brachiograph-main'))
from brachiograph import BrachioGraph

def view_json(json_path):
    """View a JSON file with turtle graphics"""

    print(f"Loading {json_path}...")

    try:
        with open(json_path, 'r') as f:
            lines = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {json_path}")
        input("Press Enter to exit...")
        return
    except Exception as e:
        print(f"Error loading JSON: {e}")
        input("Press Enter to exit...")
        return

    print(f"✓ Loaded {len(lines)} lines")

    total_segments = sum(len(line) - 1 for line in lines)
    print(f"✓ Total segments: {total_segments}")

    try:
        print("\nCreating virtual plotter with turtle graphics...")
        bg = BrachioGraph(
            virtual=True,
            turtle=True,
            inner_arm=8,
            outer_arm=8,
            bounds=(-8, 4, 8, 13),
            wait=0,
            resolution=0.5
        )

        print("Plotting...")
        bg.plot_lines(lines)

        print("\n✓ Complete! Close turtle window when done.")
    except Exception as e:
        print(f"\nError plotting: {e}")
        import traceback
        traceback.print_exc()

    input("\nPress Enter to exit...")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        json_path = sys.argv[1]
    else:
        print("Usage: python turtle_viewer.py <path-to-json>")
        json_path = input("\nOr enter path to JSON file: ")

    view_json(json_path)