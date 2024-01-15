import cv2
import numpy as np
import base64

def encode_frame_to_string(frame):
    # Compress the frame using imencode. '.jpg' specifies the compression algorithm
    ret, buffer = cv2.imencode('.jpg', frame)
    if ret:
        return base64.b64encode(buffer).decode('utf-8')
    return None

def serialize_frame(frame):
    return np.array(frame).tobytes()

def store_frame_to_redis(redis_client, factory_name, camera_id, timestamp, frame):
    key = f"frame:{factory_name}:{camera_id}:{timestamp}"
    frame_string = encode_frame_to_string(frame)

    redis_client.set(key, frame_string)

    return key

    # Set a TTL for the hash (e.g., 60 seconds)
    # redis_client.expire(key, 60)
