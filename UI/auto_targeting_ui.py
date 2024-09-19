import json
import socket

import cv2
import numpy as np
import targeting


class AutoTargeter:
    def __init__(self):
        # Load class names for PASCAL VOC
        self.class_names = []
        with open("UI/model_data/coco.names", "r") as f:
            self.class_names = [line.strip() for line in f.readlines()]

        # Load the DNN model
        self.net = cv2.dnn.readNetFromCaffe(
            "UI/model_data/MobileNetSSD_deploy.prototxt",
            "UI/model_data/MobileNetSSD_deploy.caffemodel",
        )

        # Set preferable backend and target
        self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_DEFAULT)
        self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

        # Specify the target class index for 'person' in the model
        self.person_class_id = 15  # For MobileNet SSD, 'person' class ID is 15

        # Arduino connection parameters
        self.arduino_ip = "192.168.50.30"  # Replace with your Arduino's IP address
        self.arduino_port = 80  # Replace with your Arduino's port if different

        # Create a socket object
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect to the Arduino
        try:
            self.client_socket.connect((self.arduino_ip, self.arduino_port))
            print(f"Connected to Arduino at {self.arduino_ip}:{self.arduino_port}")
        except Exception as e:
            print(f"Error connecting to Arduino: {e}")
            self.client_socket.close()
            exit(1)

    def process_image(self, frame):
        # frame_resized = cv2.resize(frame, (300, 300))
        frame_resized = frame
        blob = cv2.dnn.blobFromImage(frame_resized, 0.007843, (300, 300), 127.5)
        self.net.setInput(blob)
        detections = self.net.forward()

        h, w = frame.shape[:2]

        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > 0.65:
                class_id = int(detections[0, 0, i, 1])
                if class_id == self.person_class_id:
                    box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                    (startX, startY, endX, endY) = box.astype("int")

                    startX = max(0, min(startX, w - 1))
                    startY = max(0, min(startY, h - 1))
                    endX = max(0, min(endX, w - 1))
                    endY = max(0, min(endY, h - 1))

                    centerX = int((startX + endX) / 2)
                    centerY = int((startY + endY) / 2)

                    # Scale coordinates to 0-100
                    scaled_centerX = (centerX / w) * 100
                    scaled_centerY = (centerY / h) * 100

                    # Ensure coordinates are within 0-100
                    scaled_centerX = max(0, min(scaled_centerX, 100))
                    scaled_centerY = max(0, min(scaled_centerY, 100))

                    servo_x = targeting.map_video_x_to_servo(scaled_centerX)

                    return servo_x, scaled_centerX, scaled_centerY

        return None, None, None


# Example usage
if __name__ == "__main__":
    auto_targeter = AutoTargeter()
    cv2.namedWindow("preview")
    vc = cv2.VideoCapture(0)

    if vc.isOpened():  # Try to get the first frame
        rval, frame = vc.read()
    else:
        rval = False

    while rval:
        image_x = auto_targeter.process_image(frame)
        if image_x is not None:
            print(f"Image X: {image_x}")

        cv2.imshow("preview", frame)
        rval, frame = vc.read()
        key = cv2.waitKey(1)
        if key == 27:  # Exit on ESC
            break

    # Clean up
    cv2.destroyAllWindows()
    vc.release()
    auto_targeter.client_socket.close()
