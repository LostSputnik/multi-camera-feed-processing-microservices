import cv2
import time
import redis

from utils import store_frame_to_redis, send_key_to_queue

rc = redis.Redis(host='localhost', port=6379, decode_responses=True)

camera_links = []

network_ips = ['172.16.109.50', '172.16.109.51', '172.16.109.52', '172.16.109.53']

for ip in network_ips:
    for i in range(1, 14):
        camera_links.append(f"rtsp://admin:admin1234@{ip}:554/cam/realmonitor?channel={i}&subtype=0")


# print(camera_links)
while True:
    for i, link in enumerate(camera_links):
        cap = cv2.VideoCapture(link)
        ret, frame = cap.read()
        if ret:
            current_time = time.time()
            struct_time = time.localtime(current_time)
            time_string = time.strftime("%m_%d_%Y-%H_%M_%S", struct_time)

            # save frame to disk
            # cv2.imwrite(f'framedump/{i}_{time_string}.jpg', frame)


            # save frame to storage and get reference
            key = store_frame_to_redis(
                redis_client=rc, 
                factory_name='swapno-bashundhora-ra', 
                camera_id=i, 
                timestamp=time_string, 
                frame=frame
                )

            # Send key reference to RabbitMQ for detection service
            send_key_to_queue('localhost', 'frame_queue', key)
        
        cap.release()



