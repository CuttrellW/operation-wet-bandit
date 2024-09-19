import tkinter as tk

import command_ui
import cv2
import targeting  # Ensure this import is correct
from PIL import Image, ImageTk
from targeting import calibrate, calibrate_x_axis, calibrate_x_point


class VideoStreamApp:
    def __init__(self, root):
        self.calibration_points = 3  # Set the number of calibration points
        # initialize the command ui
        self.spoof_arduino = False
        print("Initializing Arduino Controller")
        self.arduino_controller = command_ui.ArduinoController(spoof=self.spoof_arduino)
        self.arduino_controller.connect()

        self.calibrating = False  # Add a flag to track calibration state
        self.manual_control = False  # Add a flag to track manual control mode
        self.root = root
        self.root.title("Video Stream with Mouse Tracking")

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
            text="Manual Control Mode",
            command=self.toggle_manual_control,
        )
        self.button1.pack()

        self.button2 = tk.Button(
            self.settings_frame,
            text="Calibrate X Point",
            command=calibrate_x_point(self),
        )
        self.button2.pack()

        self.button3 = tk.Button(
            self.settings_frame,
            text="Setting 3",
            command=lambda: self.target("Setting 3"),
        )
        self.button3.pack()

        self.calibrate_button = tk.Button(
            self.settings_frame,
            text="Calibrate",
            command=self.start_calibration,
        )
        self.calibrate_button.pack()

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

    def key_press(self, event):
        if self.manual_control:
            actions = {
                "Up": lambda: self.arduino_controller.update_position(
                    self.arduino_controller.x_pos,
                    self.arduino_controller.y_pos - self.arduino_controller.step_size,
                    "UP",
                )
                or self.settings_text.insert(tk.END, "Moved UP\n"),
                "Down": lambda: self.arduino_controller.update_position(
                    self.arduino_controller.x_pos,
                    self.arduino_controller.y_pos + self.arduino_controller.step_size,
                    "DOWN",
                )
                or self.settings_text.insert(tk.END, "Moved DOWN\n"),
                "Left": lambda: self.arduino_controller.update_position(
                    self.arduino_controller.x_pos - self.arduino_controller.step_size,
                    self.arduino_controller.y_pos,
                    "LEFT",
                )
                or self.settings_text.insert(tk.END, "Moved LEFT\n"),
                "Right": lambda: self.arduino_controller.update_position(
                    self.arduino_controller.x_pos + self.arduino_controller.step_size,
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
            }

            action = actions.get(event.keysym)
            if action:
                action()
            else:
                print(f"Unmapped key pressed: {event.keysym}")
                self.settings_text.insert(
                    tk.END, f"Unmapped key pressed: {event.keysym}\n"
                )

        self.settings_text.see(tk.END)

    def key_release(self, event):
        pass  # Add any necessary key release handling here

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

    def start_calibration(self):
        self.calibrating = True  # Set the flag to True when calibration starts
        self.root.update_idletasks()  # Ensure the UI updates immediately
        calibrate_x_axis(
            self
        )  # Pass the instance of VideoStreamApp to the calibrate function
        # self.calibrating = False  # Reset the flag after calibration ends

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

    def update_video(self):
        if not self.calibrating:  # Only update video if not calibrating
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
                    if self.manual_control:
                        # Draw a vertical red line mapped using map_servo_x_to_video_x. This line should only be drawn over the actual video feed, not the entire canvas.
                        servo_x = self.arduino_controller.x_pos
                        video_x = targeting.map_servo_x_to_video_x(servo_x)
                        if video_x is not None:
                            line_x = int((video_x / 100) * new_width)
                            self.video_canvas.create_line(
                                line_x,
                                (canvas_height - new_height) // 2,
                                line_x,
                                (canvas_height + new_height) // 2,
                                fill="red",
                                width=2,
                            )

        self.root.after(50, self.update_video)

    def mouse_motion(self, event):
        # Get the size of the video canvas
        width = self.video_canvas.winfo_width()
        height = self.video_canvas.winfo_height()
        # Calculate the coordinates as a scale of 0-100
        x = int((event.x / width) * 100)
        y = int((event.y / height) * 100)
        # Update the coordinates label
        self.coord_label.configure(text=f"Coordinates: ({x}, {y})")
        if self.manual_control:
            # set the target servo_x position based on the mouse x position
            servo_x = targeting.map_video_x_to_servo(x)
            if servo_x is not None:
                self.arduino_controller.update_position(
                    servo_x, self.arduino_controller.y_pos, "Mouse Tracking"
                )
                self.settings_text.insert(
                    tk.END, f"Servo position updated: x={servo_x}\n"
                )
                print(f"Servo position updated: x={servo_x}")
                self.settings_text.see(tk.END)

        # print(f"Mouse moved to ({x}, {y})")

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

    def target(self, setting):
        print(f"Button pressed: {setting}")
        self.settings_text.insert(tk.END, f"Button pressed: {setting}\n")
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
