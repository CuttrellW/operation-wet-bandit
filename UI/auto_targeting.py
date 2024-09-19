import cv2
import numpy as np

# Load class names
class_names = []
with open("model_data/coco.names", "r") as f:
    class_names = [line.strip() for line in f.readlines()]

# Load the DNN model
net = cv2.dnn.readNetFromCaffe('model_data/MobileNetSSD_deploy.prototxt',
                               'model_data/MobileNetSSD_deploy.caffemodel')

# Set preferable backend and target to avoid potential issues
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_DEFAULT)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

# Specify the target class index for 'person' in the model
person_class_id = 15  # For MobileNet SSD, 'person' class ID is 15

cv2.namedWindow("preview")
vc = cv2.VideoCapture(0)

if vc.isOpened():  # Try to get the first frame
    rval, frame = vc.read()
else:
    rval = False

while rval:
    frame_resized = cv2.resize(frame, (300, 300))
    # Prepare the frame for the neural network
    blob = cv2.dnn.blobFromImage(frame_resized, 0.007843, (300, 300), 127.5)
    net.setInput(blob)
    detections = net.forward()

    h, w = frame.shape[:2]

    # Loop over the detections
    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > 0.75:
            class_id = int(detections[0, 0, i, 1])
            if class_id == person_class_id:
                # Compute bounding box coordinates
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype('int')

                # Ensure coordinates are within the frame dimensions
                startX = max(0, min(startX, w - 1))
                startY = max(0, min(startY, h - 1))
                endX = max(0, min(endX, w - 1))
                endY = max(0, min(endY, h - 1))

                # Calculate the center x-coordinate
                centerX = int((startX + endX) / 2)
                centerY = int((startY + endY) / 2)

                # Draw the bounding box and center point
                label = f"{class_names[class_id]}: {confidence:.2f}"
                cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 255, 0), 2)
                cv2.circle(frame, (centerX, centerY), 5, (255, 0, 0), -1)
                cv2.putText(frame, label, (startX, startY - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                # Print the center x-coordinate
                print(f"Center mass: X{centerX} Y{centerY}")
                print(label)

    cv2.imshow("preview", frame)
    rval, frame = vc.read()
    key = cv2.waitKey(1)
    if key == 27:  # Exit on ESC
        break

cv2.destroyAllWindows()
vc.release()