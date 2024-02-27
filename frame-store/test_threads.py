import cv2
import time

from utils import store_frame_to_redis, send_key_to_queue

def frame_store_loop_single_camera(rtsp_link, camera_id, redis_client):
    print(f'Now monitoring camera: ', camera_id)
    last_time = time.time()

    # Initialize statistics variables
    total_wait_time = 0
    count = 0
    min_wait_time = float('inf')
    max_wait_time = 0

    # Interval for displaying statistics (e.g., every 60 seconds)
    display_interval = 60
    last_display_time = time.time()

    # init last time
    # last_time = time.time()

    while True:
        try:
            cap = cv2.VideoCapture(rtsp_link)
            ret, frame = cap.read()
        except: 
            print('failed for ', camera_id)
            continue

        if ret:
            current_time = time.time()
            struct_time = time.localtime(current_time)
            time_string = time.strftime("%m_%d_%Y-%H_%M_%S", struct_time)

            # calculate wait times
            wait_time = current_time - last_time

            # Update statistics
            total_wait_time += wait_time
            count += 1
            min_wait_time = min(min_wait_time, wait_time)
            max_wait_time = max(max_wait_time, wait_time)

            # Display statistics at regular intervals
            if current_time - last_display_time > display_interval:
                avg_wait_time = total_wait_time / count if count > 0 else 0
                print(f'Camera {camera_id}: Avg={avg_wait_time:.2f}s, Min={min_wait_time:.2f}s, Max={max_wait_time:.2f}s FramesTotal={count}')
                last_display_time = current_time
            
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

            # # for debug
            # wait_time = {current_time-last_time}
            # print(f'id: {camera_id} after: ', wait_time)
            # print(f'Sent: ', time.strftime("%H_%M_%S", struct_time), camera_id)

            # cv2.imwrite(key+'.jpg', frame)

            # update timestamp
            last_time = current_time

            # time.sleep(4)


n_camera = 30
camera_links = [f"rtsp://admin:aci54321@192.168.12.53:554/cam/realmonitor?channel={i}&subtype=0" for i in range(n_camera)]

import redis

r = redis.Redis(host='localhost', port=6379, decode_responses=True)


# TESTING
# wait_times = {}

# for i in range(n_camera):
#     wait_times[i] = []

# from threading import Thread

# threads = []

# for i in range(30):
#     threads.append(Thread(target=frame_store_loop_single_camera, args=(camera_links[i], i, r)))
#     # threads[-1].daemon 
#     threads[-1].start()
#     # frame_store_loop_single_camera(camera_links[i], i, r)



# import concurrent.futures
# with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
#     executor.map(frame_store_loop_single_camera, (camera_links, range(n_camera), [r] * n_camera))

# hile True:
#     for i in range(30):
#     frame_store_loop_single_camera(rtsp_link=camera_links[i], camera_id=i, redis_client=r)


# frame_store_loop_single_camera(rtsp_link=camera_links[0], camera_id=0, redis_client=r)
