import cv2
import numpy as np

class ObjectDetectorYOLOv4:
    """
    A class to encapsulate object detection functionality using YOLOv4.
    """

    def __init__(self, weights_path, config_path, names_path):
        """
        Initializes the ObjectDetector with paths to the model weights, configuration, and class names.

        Parameters:
            weights_path (str): The path to the YOLOv4 weights file.
            config_path (str): The path to the YOLOv4 configuration file.
            names_path (str): The path to the file containing class names.
        """
        self.net = cv2.dnn.readNet(weights_path, config_path)
        layer_names = self.net.getLayerNames()
        self.output_layers = [layer_names[i - 1] for i in self.net.getUnconnectedOutLayers().flatten()]
        self.classes = self._load_classes(names_path)

    def _load_classes(self, path):
        """Loads the class names from a file."""
        with open(path, "r") as f:
            classes = [line.strip() for line in f.readlines()]
        return classes
    
    def get_class_mapping(self):
        """
        Returns a dictionary mapping class indices to class names.
        """
        return {i: name for i, name in enumerate(self.classes)}

    def detect_objects(self, frame):
        """Detects objects in a given frame using YOLOv4."""
        blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), swapRB=True, crop=False)
        self.net.setInput(blob)
        outs = self.net.forward(self.output_layers)
        return outs

    def process_detections(self, outs, shape):
        """
        Processes the detection results and returns detected objects along with their confidence scores and class IDs.

        Parameters:
            outs (list): The output from the YOLO network.
            shape (tuple): The shape of the frame (height, width).

        """
        height, width = shape
        boxes, confidences, class_ids = [], [], []
        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                
                center_x, center_y, w, h = detection[0:4] * np.array([width, height, width, height])
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)

                boxes.append([x, y, int(w), int(h)])
                confidences.append(float(confidence))
                class_ids.append(class_id)

        indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)

        results = [{'coordinates': boxes[i], 'confidence': confidences[i], 'class_id': class_ids[i]} for i in indexes]
        return results

