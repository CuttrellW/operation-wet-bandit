import json
import tkinter as tk

import numpy as np
from scipy.interpolate import griddata

# Global variable to store the calibration mesh
calibration_mesh = {}


def map_to_servo(top_left, bottom_right):
    """
    Maps the coordinates of the center of a bounding box to servo positions.

    Args:
        top_left (tuple): (x, y) coordinates of the top left corner of the bounding box.
        bottom_right (tuple): (x, y) coordinates of the bottom right corner of the bounding box.

    Returns:
        tuple: (servo_x, servo_y) positions for the servo motor.
    """
    global calibration_mesh

    if not calibration_mesh:
        try:
            # Load the calibration mesh from the JSON file
            with open("calibration_mesh.json", "r") as f:
                calibration_mesh = json.load(f)
        except FileNotFoundError:
            print("Error: calibration_mesh.json file not found.")
            return None, None
        except json.JSONDecodeError:
            print("Error: Failed to decode JSON from calibration_mesh.json.")
            return None, None

    # Calculate the center of the bounding box
    center_x = (top_left[0] + bottom_right[0]) / 2
    center_y = (top_left[1] + bottom_right[1]) / 2

    try:
        # Extract points and values from the calibration mesh
        points = np.array(
            [list(map(float, k.split(","))) for k in calibration_mesh.keys()]
        )
        values = np.array(list(calibration_mesh.values()), dtype=float)

        # Interpolate the servo positions
        servo_x, servo_y = griddata(
            points, values, (center_x, center_y), method="linear"
        )

        # If interpolation fails (e.g., point outside convex hull), fall back to the closest point
        if np.isnan(servo_x) or np.isnan(servo_y):
            closest_point = min(
                calibration_mesh.keys(),
                key=lambda k: (float(k.split(",")[0]) - center_x) ** 2
                + (float(k.split(",")[1]) - center_y) ** 2,
            )
            servo_x, servo_y = calibration_mesh[closest_point]
    except Exception as e:
        print(f"Error during interpolation: {e}")
        return None, None

    return servo_x, servo_y


def calibrate(app):
    """
    Calibrates the system by placing a red plus sign on the video stream and waiting for the servos
    to be positioned such that the laser aligns with the plus sign. This is performed 10 times from
    left to right on the image, and 3 times from top to bottom.

    Args:
        app (VideoStreamApp): The instance of the VideoStreamApp to calibrate.
    """
    global calibration_mesh
    calibration_mesh = {}
    width = app.video_label.winfo_width()
    height = app.video_label.winfo_height()

    for i in range(3):
        for j in range(10):
            x = int(j * width / 9)
            y = int(i * height / 2)
            # Create a red plus sign using a Canvas widget
            canvas = tk.Canvas(app.video_label, width=width, height=height)
            canvas.place(x=0, y=0)
            canvas.create_line(x - 5, y, x + 5, y, fill="red")
            canvas.create_line(x, y - 5, x, y + 5, fill="red")
            app.root.update()
            app.settings_text.insert(
                tk.END, f"Align laser to ({x}, {y}) and press Enter...\n"
            )
            app.root.wait_variable(app.enter_pressed)
            print("enter pressed")
            # reset the variable
            app.enter_pressed.set(False)
            servo_x, servo_y = app.get_servo_positions()
            calibration_mesh[f"{x},{y}"] = (servo_x, servo_y)

            canvas.delete("all")
            canvas.destroy()

    app.calibration_mesh = calibration_mesh
    app.settings_text.insert(tk.END, "Calibration complete.\n")

    try:
        # Save the calibration mesh to a file
        with open("calibration_mesh.json", "w") as f:
            json.dump(calibration_mesh, f)
        app.settings_text.insert(
            tk.END, "Calibration data saved to calibration_mesh.json.\n"
        )
    except IOError:
        app.settings_text.insert(
            tk.END, "Error: Failed to save calibration data to calibration_mesh.json.\n"
        )
