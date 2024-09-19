import json
import tkinter as tk

import numpy as np
from scipy.interpolate import griddata

# Global variable to store the calibration mesh
calibration_mesh = {}


def map_video_x_to_servo(video_x):
    """
    Maps the video x-coordinate to servo positions.

    Args:
        video_x (float): x coordinate on the video stream (0 to 100).

    Returns:
        float: servo_x position for the servo motor.
    """
    global calibration_mesh

    if not calibration_mesh:
        try:
            # Load the calibration mesh from the JSON file
            with open("UI/calibration_mesh.json", "r") as f:
                calibration_mesh = json.load(f)
        except FileNotFoundError:
            print("Error: calibration_mesh.json file not found.")
            return None
        except json.JSONDecodeError:
            print("Error: Failed to decode JSON from calibration_mesh.json.")
            return None

    try:
        # Extract x points and corresponding servo values from the calibration mesh
        x_points = np.array([float(k.split(",")[0]) for k in calibration_mesh.keys()])
        servo_x_values = np.array([v[0] for v in calibration_mesh.values()])

        # Sort the x points and corresponding servo values in ascending order
        sorted_indices = np.argsort(x_points)
        x_points = x_points[sorted_indices]
        servo_x_values = servo_x_values[sorted_indices]

        # Perform linear interpolation on the x-axis
        servo_x = np.interp(video_x, x_points, servo_x_values)
    except Exception as e:
        print(f"Error during interpolation: {e}")
        return None

    return servo_x


def map_servo_x_to_video_x(servo_x):
    """
    Maps the servo positions to coordinates on the video stream.

    Args:
        servo_x (float): The servo_x position.

    Returns:
        float: x coordinate on the video stream.
    """
    global calibration_mesh

    if not calibration_mesh:
        try:
            # Load the calibration mesh from the JSON file
            with open("UI/calibration_mesh.json", "r") as f:
                calibration_mesh = json.load(f)
        except FileNotFoundError:
            print("Error: calibration_mesh.json file not found.")
            return None
        except json.JSONDecodeError:
            print("Error: Failed to decode JSON from calibration_mesh.json.")
            return None

    try:
        # Extract x points and corresponding servo values from the calibration mesh
        x_points = np.array([float(k.split(",")[0]) for k in calibration_mesh.keys()])
        servo_x_values = np.array([v[0] for v in calibration_mesh.values()])

        # Sort the x points and corresponding servo values in ascending order
        sorted_indices = np.argsort(x_points)
        x_points = x_points[sorted_indices]
        servo_x_values = servo_x_values[sorted_indices]

        # Perform linear interpolation on the x-axis
        x = np.interp(servo_x, servo_x_values, x_points)
    except Exception as e:
        print(f"Error during interpolation: {e}")
        return None

    return x


def calibrate_x_axis(app):
    """
    Calibrates the x-axis by allowing the user to click on targets in the image and set the servo_x position.

    Args:
        app (VideoStreamApp): The instance of the VideoStreamApp to calibrate.
    """
    app.calibrating = True
    calibration_mesh = {}
    app.settings_text.insert(
        tk.END,
        "Click on a target to start calibration. Complete all steps to finish.\n",
    )

    def on_mouse_click(event):
        print("mouse clicked")
        # Get the size of the video canvas
        width = app.video_canvas.winfo_width()
        height = app.video_canvas.winfo_height()
        # Calculate the coordinates as a scale of 0-100
        x = int((event.x / width) * 100)
        y = int((event.y / height) * 100)
        # Draw a red plus sign at the clicked position
        plus_sign = [
            app.video_canvas.create_line(
                event.x - 10, event.y, event.x + 10, event.y, fill="red", width=3
            ),
            app.video_canvas.create_line(
                event.x, event.y - 10, event.x, event.y + 10, fill="red", width=3
            ),
        ]
        app.root.update()
        app.settings_text.insert(
            tk.END, f"Align servo_x to ({x}, {y}) and press Enter...\n"
        )
        app.enter_pressed.set(False)  # Reset the variable before waiting
        app.root.wait_variable(app.enter_pressed)
        servo_x, _ = app.get_servo_positions()
        calibration_mesh[f"{x},{y}"] = (servo_x, 1.1)  # Only calibrating x-axis

        # Remove the plus sign after calibration step
        for item in plus_sign:
            app.video_canvas.delete(item)

    # Run the calibration process 10 times
    for _ in range(10):
        app.video_canvas.bind("<Button-1>", on_mouse_click)
        app.settings_text.insert(tk.END, "Click on the next target...\n")
        app.root.wait_variable(app.enter_pressed)

    # Save the calibration mesh to a file
    try:
        with open("UI/calibration_mesh.json", "w") as f:
            json.dump(calibration_mesh, f)
        app.settings_text.insert(tk.END, "Calibration complete and saved.\n")
    except Exception as e:
        app.settings_text.insert(tk.END, f"Error saving calibration mesh: {e}\n")
    app.calibrating = False


def calibrate(app):
    """
    Calibrates the system by placing a red plus sign on the video stream and waiting for the servos
    to be positioned such that the laser aligns with the plus sign. This is performed 10 times from
    left to right on the image, and 3 times from top to bottom.

    Args:
        app (VideoStreamApp): The instance of the VideoStreamApp to calibrate.
    """
    calibration_mesh = {}
    width = app.video_canvas.winfo_width()
    height = app.video_canvas.winfo_height()

    margin_x = int(0.1 * width)
    margin_y = int(0.1 * height)

    for i in range(3):
        for j in range(10):
            x = int(j * (width - 2 * margin_x) / 9) + margin_x
            y = int(i * (height - 2 * margin_y) / 2) + margin_y
            # Draw a larger and thicker red plus sign directly on the existing Canvas widget
            plus_sign = [
                app.video_canvas.create_line(x - 10, y, x + 10, y, fill="red", width=3),
                app.video_canvas.create_line(x, y - 10, x, y + 10, fill="red", width=3),
            ]
            app.root.update()
            app.settings_text.insert(
                tk.END, f"Align laser to ({x}, {y}) and press Enter...\n"
            )
            app.enter_pressed.set(False)  # Reset the variable before waiting
            app.root.wait_variable(app.enter_pressed)
            servo_x, servo_y = app.get_servo_positions()
            calibration_mesh[f"{x},{y}"] = (servo_x, servo_y)

            # Remove the plus sign after calibration step
            for item in plus_sign:
                app.video_canvas.delete(item)

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
