import cv2
import time
from utils import store_frame_to_redis, send_key_to_queue

def run(rtsp_link, camera_id):
    print(f'running {camera_id}')
    try:
        cap = cv2.VideoCapture(rtsp_link)
        ret, frame = cap.read()
    except: 
        print('failed for ', camera_id)
        return 

    if ret:
        current_time = time.time()
        struct_time = time.localtime(current_time)
        time_string = time.strftime("%m_%d_%Y-%H_%M_%S", struct_time)

        # calculate wait times
        wait_time[camera_id] = current_time - last_time[camera_id]

        # Update statistics
        total_wait_time[camera_id] += wait_time[camera_id]
        count[camera_id] += 1
        min_wait_time[camera_id] = min(min_wait_time[camera_id], wait_time[camera_id])
        max_wait_time[camera_id] = max(max_wait_time[camera_id], wait_time[camera_id])

        # Display statistics at regular intervals
        if current_time - last_display_time[camera_id] > display_interval:
            avg_wait_time = total_wait_time[camera_id] / count[camera_id] if count[camera_id] > 0 else 0
            print(f'Camera {camera_id}: Avg={avg_wait_time:.2f}s, Min={min_wait_time[camera_id]:.2f}s, Max={max_wait_time[camera_id]:.2f}s FramesTotal={count[camera_id]}')
            last_display_time[camera_id] = current_time
        
        # if current_time - last_time > 4:
        # save frame to storage and get reference
        key = store_frame_to_redis(
            redis_client=redis_client, 
            factory_name='pharma-ng', 
            camera_id=camera_id, 
            timestamp=time_string, 
            frame=frame
            )

        # Send key reference to RabbitMQ for detection service
        send_key_to_queue('localhost', 'frame_queue', key)


n_camera = 30
camera_links = [f"rtsp://admin:aci54321@192.168.12.53:554/cam/realmonitor?channel={i}&subtype=0" for i in range(n_camera)]

import redis

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)


last_time = [time.time() for _ in range(n_camera)]
wait_time = [0] * n_camera

# Initialize statistics variables
total_wait_time = [0] * n_camera
count = [0] * n_camera
min_wait_time = [float('inf')] * n_camera 
max_wait_time = [0] * n_camera

# Interval for displaying statistics (e.g., every 60 seconds)
display_interval = 60
last_display_time = [time.time() for _ in range(n_camera)]

while True:
    loop_time = time.time()
    for i in range(n_camera):
        run(camera_links[i], i)
    print(f'Loop End: {time.time() - loop_time}')

