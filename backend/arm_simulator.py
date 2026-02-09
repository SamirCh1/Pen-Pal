#!/usr/bin/env python3
import sys
from unittest.mock import MagicMock
sys.modules['pigpio'] = MagicMock()

import json
import os
import turtle
import math
import time

# Add brachiograph-main to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'brachiograph-main'))

def scale_lines_to_bounds(lines, bounds=(-8, 4, 8, 13)):
    """Scale lines to fit within plotter bounds"""

    if not lines:
        return lines

    # Find min/max coordinates
    all_x = [point[0] for line in lines for point in line]
    all_y = [point[1] for line in lines for point in line]

    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)

    # Calculate input dimensions
    input_width = max_x - min_x
    input_height = max_y - min_y

    # Target bounds
    target_min_x, target_min_y, target_max_x, target_max_y = bounds
    target_width = target_max_x - target_min_x
    target_height = target_max_y - target_min_y

    # Calculate scale factor (use the smaller scale to fit within bounds)
    scale_x = target_width / input_width if input_width > 0 else 1
    scale_y = target_height / input_height if input_height > 0 else 1
    scale = min(scale_x, scale_y)

    # Calculate centering offsets
    scaled_width = input_width * scale
    scaled_height = input_height * scale
    offset_x = target_min_x + (target_width - scaled_width) / 2
    offset_y = target_min_y + (target_height - scaled_height) / 2

    # Scale and translate all points
    scaled_lines = []
    for line in lines:
        scaled_line = [
            [
                (point[0] - min_x) * scale + offset_x,
                (point[1] - min_y) * scale + offset_y
            ]
            for point in line
        ]
        scaled_lines.append(scaled_line)

    print(f"Scaled from ({min_x:.1f}, {min_y:.1f}) → ({max_x:.1f}, {max_y:.1f})")
    print(f"       to ({target_min_x:.1f}, {target_min_y:.1f}) → ({target_max_x:.1f}, {target_max_y:.1f})")
    print(f"Scale factor: {scale:.4f}")

    return scaled_lines

class ArmSimulator:
    """Simulate the brachiograph arm movements"""

    def __init__(self, inner_arm=8, outer_arm=8, bounds=(-8, 4, 8, 13)):
        self.inner_arm = inner_arm
        self.outer_arm = outer_arm
        self.bounds = bounds

        # Setup screen
        self.screen = turtle.Screen()
        self.screen.setup(width=800, height=800)
        self.screen.title("BrachioGraph Arm Simulator")
        self.screen.bgcolor('white')
        self.screen.tracer(0)  # Turn off auto-update for better performance

        # Drawing turtle (for the path)
        self.pen = turtle.Turtle()
        self.pen.speed(0)
        self.pen.penup()
        self.pen.hideturtle()

        # Arm visualization turtles (reusable)
        self.arm_base = turtle.Turtle()
        self.arm_base.hideturtle()
        self.arm_base.speed(0)

        self.arm_inner = turtle.Turtle()
        self.arm_inner.hideturtle()
        self.arm_inner.speed(0)

        self.arm_outer = turtle.Turtle()
        self.arm_outer.hideturtle()
        self.arm_outer.speed(0)

        # Current state
        self.current_x = 0
        self.current_y = 10
        self.pen_down = False

    def draw_arm(self, shoulder_pos, elbow_pos, pen_pos, pen_down):
        """Draw the robot arm"""

        # Convert to screen coordinates
        scale = 30  # pixels per cm
        origin_x, origin_y = 0, -200

        shoulder_x = origin_x
        shoulder_y = origin_y
        elbow_x = origin_x + elbow_pos[0] * scale
        elbow_y = origin_y + elbow_pos[1] * scale
        pen_x = origin_x + pen_pos[0] * scale
        pen_y = origin_y + pen_pos[1] * scale

        # Clear and draw base
        self.arm_base.clear()
        self.arm_base.penup()
        self.arm_base.goto(shoulder_x, shoulder_y)
        self.arm_base.dot(20, 'black')

        # Clear and draw inner arm (shoulder to elbow)
        self.arm_inner.clear()
        self.arm_inner.penup()
        self.arm_inner.goto(shoulder_x, shoulder_y)
        self.arm_inner.pendown()
        self.arm_inner.pensize(8)
        self.arm_inner.color('blue')
        self.arm_inner.goto(elbow_x, elbow_y)
        self.arm_inner.dot(15, 'blue')

        # Clear and draw outer arm (elbow to pen)
        self.arm_outer.clear()
        self.arm_outer.penup()
        self.arm_outer.goto(elbow_x, elbow_y)
        self.arm_outer.pendown()
        self.arm_outer.pensize(6)
        self.arm_outer.color('red')
        self.arm_outer.goto(pen_x, pen_y)

        # Draw pen
        pen_color = 'green' if pen_down else 'gray'
        self.arm_outer.dot(12, pen_color)

    def xy_to_angles(self, x, y):
        """Convert XY to servo angles using inverse kinematics"""
        hypotenuse = math.sqrt(x**2 + y**2)

        if hypotenuse > (self.inner_arm + self.outer_arm):
            return None, None

        if hypotenuse == 0:
            return 0, 0

        hypotenuse_angle = math.asin(x / hypotenuse)

        inner_angle = math.acos(
            (hypotenuse**2 + self.inner_arm**2 - self.outer_arm**2) /
            (2 * hypotenuse * self.inner_arm)
        )

        outer_angle = math.acos(
            (self.inner_arm**2 + self.outer_arm**2 - hypotenuse**2) /
            (2 * self.inner_arm * self.outer_arm)
        )

        shoulder_angle = hypotenuse_angle - inner_angle
        elbow_angle = math.pi - outer_angle

        return shoulder_angle, elbow_angle

    def angles_to_positions(self, shoulder_angle, elbow_angle):
        """Calculate positions of shoulder, elbow, and pen"""
        # Elbow position
        elbow_x = self.inner_arm * math.sin(shoulder_angle)
        elbow_y = self.inner_arm * math.cos(shoulder_angle)

        # Pen position
        pen_x = elbow_x + self.outer_arm * math.sin(shoulder_angle + elbow_angle)
        pen_y = elbow_y + self.outer_arm * math.cos(shoulder_angle + elbow_angle)

        return (0, 0), (elbow_x, elbow_y), (pen_x, pen_y)

    def move_to(self, x, y, draw=False):
        """Move to position and update visualization"""
        shoulder_angle, elbow_angle = self.xy_to_angles(x, y)

        if shoulder_angle is None:
            # Silently skip out of reach points
            return

        # Get positions
        shoulder_pos, elbow_pos, pen_pos = self.angles_to_positions(shoulder_angle, elbow_angle)

        # Update drawing pen
        scale = 30
        origin_x, origin_y = 0, -200
        screen_x = origin_x + pen_pos[0] * scale
        screen_y = origin_y + pen_pos[1] * scale

        if draw and self.pen_down:
            self.pen.goto(screen_x, screen_y)
        else:
            self.pen.penup()
            self.pen.goto(screen_x, screen_y)
            if self.pen_down:
                self.pen.pendown()

        # Draw arm
        self.draw_arm(shoulder_pos, elbow_pos, pen_pos, self.pen_down)

        # Update screen
        self.screen.update()

        self.current_x = x
        self.current_y = y

        # Small delay to see movement
        time.sleep(0.005)

    def penup(self):
        self.pen_down = False
        self.pen.penup()

    def pendown(self):
        self.pen_down = True
        self.pen.pendown()

    def plot_lines(self, lines):
        """Plot lines with arm visualization"""

        # Scale lines to fit bounds
        scaled_lines = scale_lines_to_bounds(lines, self.bounds)

        print(f"\nPlotting {len(scaled_lines)} lines...")

        for i, line in enumerate(scaled_lines):
            if i % 50 == 0:
                print(f"Progress: {i}/{len(scaled_lines)} lines")

            if not line:
                continue

            # Move to start of line
            start_x, start_y = line[0]
            self.penup()
            self.move_to(start_x, start_y)

            # Draw line
            self.pendown()
            for point in line[1:]:
                x, y = point
                self.move_to(x, y, draw=True)

            self.penup()

        print("✓ Complete!")

def simulate_json(json_path):
    """Simulate plotting a JSON file"""

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

    try:
        sim = ArmSimulator(inner_arm=8, outer_arm=8, bounds=(-6, 6, 6, 12))
        sim.plot_lines(lines)

        print("\n✓ Simulation complete! Close window to exit.")
        turtle.done()

    except Exception as e:
        print(f"\nError simulating: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        json_path = sys.argv[1]
    else:
        print("Usage: python arm_simulator.py <path-to-json>")
        json_path = input("\nOr enter path to JSON file: ")

    simulate_json(json_path)