import sys
from unittest.mock import MagicMock
sys.modules['pigpio'] = MagicMock()

import json
sys.path.insert(0, 'brachiograph-main')
from brachiograph import BrachioGraph

def test_json_file(json_path):
    """Test a JSON file with turtle graphics"""

    print(f"Loading {json_path}...")

    with open(json_path, 'r') as f:
        lines = json.load(f)

    print(f"✓ Loaded {len(lines)} lines")

    print("Creating virtual plotter with turtle graphics...")
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

    print("✓ Complete! Close turtle window when done.")
    input("Press Enter to exit...")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        json_path = sys.argv[1]
    else:
        json_path = input("Enter path to JSON file: ")

    test_json_file(json_path)