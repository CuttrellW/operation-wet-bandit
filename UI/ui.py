import tkinter as tk

import cv2
import targeting  # Ensure this import is correct
from PIL import Image, ImageTk
from targeting import calibrate, calibrate_x_axis


class VideoStreamApp:
    def __init__(self, root):
        self.calibrating = False  # Add a flag to track calibration state
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
        self.settings_text = tk.Text(self.settings_frame, height=10, width=30)
        self.settings_text.pack()

        # Create labels to display the coordinates
        self.coord_label = tk.Label(self.settings_frame, text="Coordinates: (0, 0)")
        self.coord_label.pack()

        # Create buttons for settings
        self.button1 = tk.Button(
            self.settings_frame,
            text="Setting 1",
            command=lambda: self.target("Setting 1"),
        )
        self.button1.pack()

        self.button2 = tk.Button(
            self.settings_frame,
            text="Setting 2",
            command=lambda: self.target("Setting 2"),
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

    def start_calibration(self):
        self.calibrating = True  # Set the flag to True when calibration starts
        self.root.update_idletasks()  # Ensure the UI updates immediately
        calibrate_x_axis(
            self
        )  # Pass the instance of VideoStreamApp to the calibrate function
        # self.calibrating = False  # Reset the flag after calibration ends

    def get_servo_positions(self):
        # Dummy implementation for example purposes
        return (0, 0)

    def on_enter_pressed(self, event):
        self.enter_pressed.set(True)

    def update_video(self):
        if not self.calibrating:  # Only update video if not calibrating
            print(self.calibrating)
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

    def target(self, setting):
        print(f"Button pressed: {setting}")
        self.settings_text.insert(tk.END, f"Button pressed: {setting}\n")

    def __del__(self):
        # Release the video capture when the app is closed
        if self.cap.isOpened():
            self.cap.release()
        # print("Video capture released")


if __name__ == "__main__":
    root = tk.Tk()
    app = VideoStreamApp(root)
    root.bind("<Return>", app.on_enter_pressed)
    root.mainloop()
