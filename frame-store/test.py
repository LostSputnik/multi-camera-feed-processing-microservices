import cv2
import time

from utils import store_frame_to_redis, send_key_to_queue

def frame_store_loop_single_camera(rtsp_link, camera_id, redis_client):
    # init last time
    last_time = time.time()
    # last_time = time.localtime(last_time)
    # last_time = time.strftime("%m_%d_%Y-%H_%M_%S", last_time)

    while True:
        cap = cv2.VideoCapture(rtsp_link)
        ret, frame = cap.read()
        if ret:
            current_time = time.time()
            struct_time = time.localtime(current_time)
            time_string = time.strftime("%m_%d_%Y-%H_%M_%S", struct_time)
            
            if current_time - last_time > 60:
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

                # update timestamp
                last_time = time_string


                # # for debug
                print(f'Sent: ', time_string, camera_id)
                cv2.imwrite(key+'.jpg', frame)



camera_links = [f"rtsp://admin:admin123@192.168.12.53:554/cam/realmonitor?channel={i}&subtype=0" for i in range(30)]
                
import redis

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

from threading import Thread
threads = []

for i in range(30):
    threads.append(Thread(target=frame_store_loop_single_camera, args=(camera_links[i], i, r)))
    # threads[-1].daemon 
    threads[-1].start()
    # frame_store_loop_single_camera(camera_links[i], i, r)


# hile True:
#     for i in range(30):
#     frame_store_loop_single_camera(rtsp_link=camera_links[i], camera_id=i, redis_client=r)


frame_store_loop_single_camera(rtsp_link=camera_links[0], camera_id=0, redis_client=r)
