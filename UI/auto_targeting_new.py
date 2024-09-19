import cv2
import numpy as np
import socket
import json

# Load class names for PASCAL VOC
class_names = []
with open("model_data/coco.names", "r") as f:
    class_names = [line.strip() for line in f.readlines()]

# Load the DNN model
net = cv2.dnn.readNetFromCaffe('model_data/MobileNetSSD_deploy.prototxt',
                               'model_data/MobileNetSSD_deploy.caffemodel')

# Set preferable backend and target
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_DEFAULT)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

# Specify the target class index for 'person' in the model
person_class_id = 15  # For MobileNet SSD, 'person' class ID is 15

# Global calibration mesh
calibration_mesh = {}

def map_to_servo_center(center_x, center_y):
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

    try:
        # Extract x and y points and corresponding servo values from the calibration mesh
        x_points = np.array([float(k.split(",")[0]) for k in calibration_mesh.keys()])
        y_points = np.array([float(k.split(",")[1]) for k in calibration_mesh.keys()])
        servo_x_values = np.array([v[0] for v in calibration_mesh.values()])
        servo_y_values = np.array([v[1] for v in calibration_mesh.values()])

        # Perform linear interpolation on the x-axis
        servo_x = np.interp(center_x, x_points, servo_x_values)
        # Perform linear interpolation on the y-axis
        servo_y = np.interp(center_y, y_points, servo_y_values)
    except Exception as e:
        print(f"Error during interpolation: {e}")
        return None, None

    return servo_x, servo_y

# Arduino connection parameters
arduino_ip = "192.168.50.30"  # Replace with your Arduino's IP address
arduino_port = 80             # Replace with your Arduino's port if different

# Create a socket object
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to the Arduino
try:
    client_socket.connect((arduino_ip, arduino_port))
    print(f"Connected to Arduino at {arduino_ip}:{arduino_port}")
except Exception as e:
    print(f"Error connecting to Arduino: {e}")
    client_socket.close()
    exit(1)

# Function to send commands to Arduino
def send_command(command):
    try:
        # Add newline character as Arduino expects
        client_socket.sendall((command + "\n").encode("utf-8"))
    except Exception as e:
        print(f"Error sending command: {e}")

cv2.namedWindow("preview")
vc = cv2.VideoCapture(0)

if vc.isOpened():  # Try to get the first frame
    rval, frame = vc.read()
else:
    rval = False

while rval:
    frame_resized = cv2.resize(frame, (300, 300))
    blob = cv2.dnn.blobFromImage(frame_resized, 0.007843, (300, 300), 127.5)
    net.setInput(blob)
    detections = net.forward()

    h, w = frame.shape[:2]

    # Variables to store servo positions
    servo_x, servo_y = None, None

    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > 0.5:
            class_id = int(detections[0, 0, i, 1])
            if class_id == person_class_id:
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype('int')

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

                servo_x, servo_y = map_to_servo_center(scaled_centerX, scaled_centerY)

                servo_x = 100 - servo_x
                if servo_x is not None and servo_y is not None:
                    # Send servo positions to Arduino
                    command = f"x={servo_x}&y={servo_y}"
                    send_command(command)
                    print(f"Sent command to Arduino: {command}")

                label = f"{class_names[class_id]}: {confidence:.2f}"
                cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 255, 0), 2)
                cv2.circle(frame, (centerX, centerY), 5, (255, 0, 0), -1)
                cv2.putText(frame, label, (startX, startY - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                # Break after processing one person (optional)
                # break

    cv2.imshow("preview", frame)
    rval, frame = vc.read()
    key = cv2.waitKey(1)
    if key == 27:  # Exit on ESC
        break

# Clean up
cv2.destroyAllWindows()
vc.release()
client_socket.close()