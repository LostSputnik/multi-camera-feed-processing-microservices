import cv2
import numpy as np

# Load YOLO
net = cv2.dnn.readNet("yolov4.weights", "yolov4.cfg")
layer_names = net.getLayerNames()
output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers().flatten()]

# Load the COCO class labels our YOLO model was trained on
classes = []
with open("coco.names", "r") as f:
    classes = [line.strip() for line in f.readlines()]

def detect_person_cv2_yolov4(frame): 
    # store frame shape
    height, width, channels = frame.shape

    # Detecting objects
    blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
    net.setInput(blob)
    outs = net.forward(output_layers)

    # Information to display on the frame
    class_ids = []
    confidences = []
    boxes = []
    locations = []
    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5 and class_id == 0:  # Filter for person class
                # Object detected
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)

                # Rectangle coordinates
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)

                # Person co-ordinates for transform
                leg_x = center_x
                leg_y = center_y + h/2

                locations.append([leg_x, leg_y])
                boxes.append([x, y, w, h])
                confidences.append(float(confidence))
                class_ids.append(class_id)

    # Apply Non-Max Suppression
    indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)

    # Draw bounding boxes on the frame
    for i in range(len(boxes)):
        if i in indexes:
            x, y, w, h = boxes[i]
            leg_x, leg_y = locations[i]
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.circle(frame, [int(leg_x),int(leg_y)], radius=6, color=(0, 0, 255), thickness=-1)


    # Display the resulting frame
    cv2.imshow("Frame", frame)

    # Break the loop
    if cv2.waitKey(0) & 0xFF == ord('q'):
        exit()


import glob
frame_paths = glob.glob('../../frame-store/framedump/*')

for frame_path in frame_paths:
    frame = cv2.imread(frame_path)
    detect_person_cv2_yolov4(frame)

