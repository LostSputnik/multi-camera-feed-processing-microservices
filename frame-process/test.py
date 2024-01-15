import cv2

from utils import retrieve_frame_from_redis
import redis

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

key = 'frame:pharma-ng:0:01_14_2024-17_45_00'

frame = retrieve_frame_from_redis(r, key)

# cv2.imwrite(key+'.jpg', frame)
