import json
import cv2
import base64
import numpy as np


def delete_frame_from_redis(redis_client, key):
    redis_client.delete(key)

def deserialize_frame_opencv(serialized_frame):
    string = base64.b64decode(serialized_frame)
    jpg_as_np = np.frombuffer(string, dtype=np.uint8)
    frame = cv2.imdecode(jpg_as_np, cv2.IMREAD_COLOR)
    return frame

def retrieve_frame_from_redis(redis_client, key):
    serialized_data = redis_client.get(key)
    data = json.loads(serialized_data)
    # print(data)
    if data:
        serialized_frame = data['frame']
        frame = deserialize_frame_opencv(serialized_frame)
        return frame
    return None