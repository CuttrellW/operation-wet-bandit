import json
import tkinter as tk

import auto_targeting_ui
import command_ui
import cv2
import targeting  # Ensure this import is correct
from PIL import Image, ImageTk
from targeting import calibrate, calibrate_x_axis, calibrate_x_point


class VideoStreamApp:
    def __init__(self, root):
        self.calibration_points = 3  # Set the number of calibration points
        self.recticle_color = "green"  # Set the color of the recticle
        # initialize the command ui
        self.spoof_arduino = False
        print("Initializing Arduino Controller")
        self.arduino_controller = command_ui.ArduinoController(spoof=self.spoof_arduino)
        self.arduino_controller.connect()

        self.calibrating = False  # Add a flag to track calibration state
        self.manual_control = False  # Add a flag to track manual control mode
        self.mouse_control = False  # Add a flag to track mouse control mode
        self.auto_targeting = False  # Initialize auto-targeting flag
        self.root = root
        self.root.title("Video Stream with Mouse Tracking and Auto Targeting")

        # Create a main frame to hold the video and settings frames
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Create a frame to hold the video on the left side
        self.video_frame = tk.Frame(self.main_frame)
        self.video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Create a canvas to display the video stream
        self.video_canvas = tk.Canvas(self.video_frame)
        self.video_canvas.pack(fill=tk.BOTH, expand=True)

        # Center the video and have it fill the canvas
        self.video_canvas.update_idletasks()
        canvas_width = self.video_canvas.winfo_width()
        canvas_height = self.video_canvas.winfo_height()
        self.video_canvas.create_image(
            canvas_width // 2, canvas_height // 2, anchor=tk.CENTER
        )

        # Create a frame to hold the settings and readout on the right side
        self.settings_frame = tk.Frame(self.main_frame)
        self.settings_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Create a text box to display the settings and readout
        self.settings_text = tk.Text(self.settings_frame, height=20, width=40)
        self.settings_text.pack()

        # Add a scrollbar to the settings_text
        self.scrollbar = tk.Scrollbar(
            self.settings_frame, command=self.settings_text.yview
        )
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.settings_text.config(yscrollcommand=self.scrollbar.set)

        # Create labels to display the coordinates
        self.coord_label = tk.Label(self.settings_frame, text="Coordinates: (0, 0)")
        self.coord_label.pack()

        # Create buttons for settings
        self.button1 = tk.Button(
            self.settings_frame,
            text="Toggle Manual Control",
            command=self.toggle_manual_control,
        )
        self.button1.pack()

        self.button3 = tk.Button(
            self.settings_frame,
            text="Toggle Mouse Targeting",
            command=self.toggle_mouse_control,
        )
        self.button3.pack()

        self.auto_target_button = tk.Button(
            self.settings_frame,
            text="Toggle Auto Targeting",
            command=self.toggle_auto_targeting,
        )
        self.auto_target_button.pack()

        # Initialize video capture
        self.cap = cv2.VideoCapture(0)

        # Bind mouse motion to the video canvas
        self.video_canvas.bind("<Motion>", self.mouse_motion)

        # Bind mouse click to the video canvas
        self.video_canvas.bind("<Button-1>", self.mouse_click)

        # Start the video loop
        self.update_video()

        # Variable to track Enter key press
        self.enter_pressed = tk.BooleanVar()

        # Bind keyboard events for manual control
        self.root.bind("<KeyPress>", self.key_press)
        self.root.bind("<KeyRelease>", self.key_release)

    def toggle_manual_control(self):
        self.manual_control = not self.manual_control
        if self.manual_control:
            self.settings_text.insert(tk.END, "Manual Control Mode: ON\n")
        else:
            self.settings_text.insert(tk.END, "Manual Control Mode: OFF\n")
        self.settings_text.see(tk.END)  # Scroll to the end

    def toggle_mouse_control(self):
        self.mouse_control = not self.mouse_control
        if self.mouse_control:
            self.settings_text.insert(tk.END, "Mouse Control Mode: ON\n")
        else:
            self.settings_text.insert(tk.END, "Mouse Control Mode: OFF\n")
        self.settings_text.see(tk.END)

    def key_press(self, event):
        if self.manual_control:
            actions = {
                "Up": lambda: self.arduino_controller.update_position(
                    self.arduino_controller.x_pos,
                    self.arduino_controller.y_pos + self.arduino_controller.step_size,
                    "UP",
                )
                or self.settings_text.insert(tk.END, "Moved UP\n"),
                "Down": lambda: self.arduino_controller.update_position(
                    self.arduino_controller.x_pos,
                    self.arduino_controller.y_pos - self.arduino_controller.step_size,
                    "DOWN",
                )
                or self.settings_text.insert(tk.END, "Moved DOWN\n"),
                "Left": lambda: self.arduino_controller.update_position(
                    self.arduino_controller.x_pos + self.arduino_controller.step_size,
                    self.arduino_controller.y_pos,
                    "LEFT",
                )
                or self.settings_text.insert(tk.END, "Moved LEFT\n"),
                "Right": lambda: self.arduino_controller.update_position(
                    self.arduino_controller.x_pos - self.arduino_controller.step_size,
                    self.arduino_controller.y_pos,
                    "RIGHT",
                )
                or self.settings_text.insert(tk.END, "Moved RIGHT\n"),
                "q": lambda: self.arduino_controller.update_position(225, 45, "UP-LEFT")
                or self.settings_text.insert(tk.END, "Moved UP-LEFT\n"),
                "e": lambda: self.arduino_controller.update_position(45, 45, "UP-RIGHT")
                or self.settings_text.insert(tk.END, "Moved UP-RIGHT\n"),
                "w": lambda: self.arduino_controller.update_position(
                    135, 45, "UP-CENTER"
                )
                or self.settings_text.insert(tk.END, "Moved UP-CENTER\n"),
                "a": lambda: self.arduino_controller.update_position(
                    225, 0, "DOWN-LEFT"
                )
                or self.settings_text.insert(tk.END, "Moved DOWN-LEFT\n"),
                "d": lambda: self.arduino_controller.update_position(
                    45, 0, "DOWN-RIGHT"
                )
                or self.settings_text.insert(tk.END, "Moved DOWN-RIGHT\n"),
                "s": lambda: self.arduino_controller.update_position(
                    135, 0, "DOWN-CENTER"
                )
                or self.settings_text.insert(tk.END, "Moved DOWN-CENTER\n"),
                "space": lambda: self.arduino_controller.toggle_solenoid()
                or self.settings_text.insert(tk.END, "Toggled Solenoid\n"),
                "c": lambda: self.record_calibration_point(event)
                or self.settings_text.insert(tk.END, "Recorded Calibration Point\n"),
            }

            action = actions.get(event.keysym)
            if action:
                action()
            else:
                print(f"Unmapped key pressed: {event.keysym}")
                self.settings_text.insert(
                    tk.END, f"Unmapped key pressed: {event.keysym}\n"
                )

    def mouse_motion(self, event):
        if self.mouse_control:
            # Get the size of the video canvas
            width = self.video_canvas.winfo_width()
            height = self.video_canvas.winfo_height()
            # Calculate the coordinates as a scale of 0-100
            x = int((event.x / width) * 100)
            y = int((event.y / height) * 100)
            # Print the coordinates to the settings_text
            self.settings_text.insert(tk.END, f"Mouse moved to: ({x}, {y})\n")
            # target the servo to the mouse position
            new_x = targeting.map_video_x_to_servo(x)
            # new y will be a math function, mapping values from 50-30 to 0-30.
            new_y = 30 - (y - 50) * 0.6

            self.arduino_controller.update_position(new_x, new_y, "Mouse Control")
            self.settings_text.see(tk.END)

    def toggle_auto_targeting(self):
        self.auto_targeting = not self.auto_targeting
        if self.auto_targeting:
            self.settings_text.insert(tk.END, "Auto Targeting: ON\n")
            self.auto_targeter = auto_targeting_ui.AutoTargeter()
        else:
            self.settings_text.insert(tk.END, "Auto Targeting: OFF\n")
        self.settings_text.see(tk.END)

    def key_release(self, event):
        pass  # Add any necessary key release handling here

    def record_calibration_point(self, event):
        # record the current mouse position and current servo_x position as a calibration point
        video_x = int((event.x / self.video_canvas.winfo_width()) * 100)
        servo_x = self.arduino_controller.x_pos
        # Ensure calibration_points is a dictionary, not an int
        if not isinstance(self.calibration_points, dict):
            self.calibration_points = {}
        self.calibration_points[f"{video_x}, 30"] = (servo_x, 30)
        # save the calibration point to UI/calibration_mesh.json
        with open("UI/calibration_mesh.json", "w") as f:
            json.dump(self.calibration_points, f)
        self.settings_text.insert(
            tk.END, f"Calibrated video_x: {video_x} with servo_x: {servo_x}\n"
        )

    def update_servo_position(self, delta_x, delta_y):
        # Update servo positions based on delta_x and delta_y
        # This is a placeholder implementation
        print(f"Updating servo position by ({delta_x}, {delta_y})")
        new_x = self.arduino_controller.x_pos + delta_x
        new_y = self.arduino_controller.y_pos + delta_y
        self.arduino_controller.update_position(new_x, new_y, "Manual Control")
        self.settings_text.insert(
            tk.END, f"Servo position updated by ({delta_x}, {delta_y})\n"
        )
        print(f"Servo position updated by ({delta_x}, {delta_y})")
        print(
            f"New servo position: ({self.arduino_controller.x_pos}, {self.arduino_controller.y_pos})"
        )
        self.settings_text.see(tk.END)  # Scroll to the end

    def get_servo_positions(self):
        # Return the current servo positions
        return (self.arduino_controller.x_pos, self.arduino_controller.y_pos)

    def print_servo_positions(self):
        x, y = self.get_servo_positions()
        self.settings_text.insert(tk.END, f"Servo positions: x={x}, y={y}\n")
        print(f"Servo positions: x={x}, y={y}")
        self.settings_text.see(tk.END)  # Scroll to the end

    def on_enter_pressed(self, event):
        self.enter_pressed.set(True)

    # Toggle recticle color function
    def toggle_recticle_color(self):
        if self.recticle_color == "green":
            self.recticle_color = "red"
        else:
            self.recticle_color = "green"
        # self.settings_text.insert(tk.END, "Toggled Recticle Color\n")

    def update_video(self, verbose=False):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)

            # Resize the image to fit the canvas while keeping the aspect ratio
            canvas_width = self.video_canvas.winfo_width()
            canvas_height = self.video_canvas.winfo_height()

            if (
                canvas_width > 0 and canvas_height > 0
            ):  # Ensure width and height are > 0
                img_ratio = img.width / img.height
                canvas_ratio = canvas_width / canvas_height

                if img_ratio > canvas_ratio:
                    new_width = canvas_width
                    new_height = int(canvas_width / img_ratio)
                else:
                    new_height = canvas_height
                    new_width = int(canvas_height * img_ratio)

                img = img.resize((new_width, new_height), Image.LANCZOS)

                imgtk = ImageTk.PhotoImage(image=img)
                self.video_canvas.imgtk = imgtk
                self.video_canvas.update_idletasks()
                self.video_canvas.create_image(
                    canvas_width // 2,
                    canvas_height // 2,
                    anchor=tk.CENTER,
                    image=imgtk,
                )
                if self.auto_targeting:
                    self.root.bind(
                        "<space>",
                        lambda event: [
                            self.arduino_controller.toggle_solenoid(),
                            self.toggle_recticle_color(),
                        ][1],
                    )

                    # Auto-targeting logic
                    person_x, crosshair_x, crosshair_y = (
                        self.auto_targeter.process_image(frame)
                    )
                    if (
                        person_x is not None
                        and crosshair_x is not None
                        and crosshair_y is not None
                    ):

                        # translate crosshair_x and crosshair_y to video coordinates
                        crosshair_x = int((crosshair_x / 100) * canvas_width)
                        crosshair_y = int((crosshair_y / 100) * canvas_height)

                        self.arduino_controller.update_position(
                            person_x, self.arduino_controller.y_pos, "Auto Targeting"
                        )
                        if verbose:
                            self.settings_text.insert(
                                tk.END,
                                f"Auto-targeting updated position to x={person_x}\n",
                            )
                        self.settings_text.see(tk.END)
                        # Draw crosshair on the video canvas
                        self.video_canvas.delete("crosshair")
                        self.video_canvas.create_line(
                            crosshair_x - 15,
                            crosshair_y,
                            crosshair_x - 5,
                            crosshair_y,
                            fill=self.recticle_color,
                            width=3,
                            tags="crosshair",
                        )
                        self.video_canvas.create_line(
                            crosshair_x + 5,
                            crosshair_y,
                            crosshair_x + 15,
                            crosshair_y,
                            fill=self.recticle_color,
                            width=3,
                            tags="crosshair",
                        )
                        self.video_canvas.create_line(
                            crosshair_x,
                            crosshair_y - 15,
                            crosshair_x,
                            crosshair_y - 5,
                            fill=self.recticle_color,
                            width=3,
                            tags="crosshair",
                        )
                        self.video_canvas.create_line(
                            crosshair_x,
                            crosshair_y + 5,
                            crosshair_x,
                            crosshair_y + 15,
                            fill=self.recticle_color,
                            width=3,
                            tags="crosshair",
                        )

                elif self.manual_control:
                    self.root.bind(
                        "<Up>",
                        lambda event: self.arduino_controller.update_position(
                            self.arduino_controller.x_pos,
                            self.arduino_controller.y_pos
                            + self.arduino_controller.step_size,
                            "UP",
                        )
                        or self.settings_text.insert(tk.END, "Moved UP\n"),
                    )
                    self.root.bind(
                        "<Down>",
                        lambda event: self.arduino_controller.update_position(
                            self.arduino_controller.x_pos,
                            self.arduino_controller.y_pos
                            - self.arduino_controller.step_size,
                            "DOWN",
                        )
                        or self.settings_text.insert(tk.END, "Moved DOWN\n"),
                    )
                    self.root.bind(
                        "<Left>",
                        lambda event: self.arduino_controller.update_position(
                            self.arduino_controller.x_pos
                            + self.arduino_controller.step_size,
                            self.arduino_controller.y_pos,
                            "LEFT",
                        )
                        or self.settings_text.insert(tk.END, "Moved LEFT\n"),
                    )
                    self.root.bind(
                        "<Right>",
                        lambda event: self.arduino_controller.update_position(
                            self.arduino_controller.x_pos
                            - self.arduino_controller.step_size,
                            self.arduino_controller.y_pos,
                            "RIGHT",
                        )
                        or self.settings_text.insert(tk.END, "Moved RIGHT\n"),
                    )
                    self.root.bind(
                        "q",
                        lambda event: self.arduino_controller.update_position(
                            225, 45, "UP-LEFT"
                        )
                        or self.settings_text.insert(tk.END, "Moved UP-LEFT\n"),
                    )
                    self.root.bind(
                        "e",
                        lambda event: self.arduino_controller.update_position(
                            45, 45, "UP-RIGHT"
                        )
                        or self.settings_text.insert(tk.END, "Moved UP-RIGHT\n"),
                    )
                    self.root.bind(
                        "w",
                        lambda event: self.arduino_controller.update_position(
                            135, 45, "UP-CENTER"
                        )
                        or self.settings_text.insert(tk.END, "Moved UP-CENTER\n"),
                    )
                    self.root.bind(
                        "a",
                        lambda event: self.arduino_controller.update_position(
                            225, 0, "DOWN-LEFT"
                        )
                        or self.settings_text.insert(tk.END, "Moved DOWN-LEFT\n"),
                    )
                    self.root.bind(
                        "d",
                        lambda event: self.arduino_controller.update_position(
                            45, 0, "DOWN-RIGHT"
                        )
                        or self.settings_text.insert(tk.END, "Moved DOWN-RIGHT\n"),
                    )
                    self.root.bind(
                        "s",
                        lambda event: self.arduino_controller.update_position(
                            135, 0, "DOWN-CENTER"
                        )
                        or self.settings_text.insert(tk.END, "Moved DOWN-CENTER\n"),
                    )
                    self.root.bind(
                        "<space>",
                        lambda event: (
                            self.arduino_controller.toggle_solenoid()
                            or self.settings_text.insert(tk.END, "Toggled Solenoid\n"),
                            setattr(
                                self,
                                "recticle_color",
                                "red" if self.recticle_color == "green" else "green",
                            ),
                        ),
                    )
        self.root.after(50, self.update_video)

    def mouse_click(self, event):
        # Get the size of the video canvas
        width = self.video_canvas.winfo_width()
        height = self.video_canvas.winfo_height()
        # Calculate the coordinates as a scale of 0-100
        x = int((event.x / width) * 100)
        y = int((event.y / height) * 100)
        # Print the coordinates to the settings_text
        self.settings_text.insert(tk.END, f"Mouse clicked at: ({x}, {y})\n")
        print(f"Mouse clicked at ({x}, {y})")
        self.settings_text.see(tk.END)  # Scroll to the end

    def __del__(self):
        # Release the video capture when the app is closed
        if self.cap.isOpened():
            self.cap.release()
        # print("Video capture released")


if __name__ == "__main__":
    spoof_arduino = True
    root = tk.Tk()
    app = VideoStreamApp(root)
    root.bind("<Return>", app.on_enter_pressed)
    root.mainloop()
