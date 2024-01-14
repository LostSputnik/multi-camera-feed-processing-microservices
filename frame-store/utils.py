import json
import cv2
import numpy as np
import base64

def serialize_frame_opencv(frame):
    # Compress the frame using imencode. '.jpg' specifies the compression algorithm
    ret, buffer = cv2.imencode('.jpg', frame)
    if ret:
        return base64.b64encode(buffer).decode('utf-8')
    return None

def serialize_frame(frame):
    return np.array(frame).tobytes()

def store_frame_to_redis(redis_client, factory_name, camera_id, timestamp, frame):
    key = f"frame:{factory_name}:{camera_id}:{timestamp}"
    serialized_frame = serialize_frame_opencv(frame)

    data = {
        "factory_name": factory_name,
        "camera_id": camera_id,
        "timestamp": timestamp,
        "frame": serialized_frame
    }

    serialized_data = json.dumps(data)

    # Store data in a hash
    redis_client.set(key, serialized_data)

    return key

    # Set a TTL for the hash (e.g., 60 seconds)
    # redis_client.expire(key, 60)
