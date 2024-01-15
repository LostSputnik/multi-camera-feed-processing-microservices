import cv2
import time

from utils import store_frame_to_redis

def frame_store_loop_single_camera(rtsp_link, camera_id, redis_client):
    # init last time
    last_time = time.time()
    last_time = time.localtime(last_time)
    last_time = time.strftime("%m_%d_%Y-%H_%M_%S", last_time)

    # init camera feed
    cap = cv2.VideoCapture(rtsp_link)
    
    while True:
        ret, frame = cap.read()
        if ret:
            timestamp = time.time()
            struct_time = time.localtime(timestamp)
            time_string = time.strftime("%m_%d_%Y-%H_%M_%S", struct_time)
            
            if last_time != time_string:
                # save frame to storage and get reference
                key = store_frame_to_redis(
                    redis_client=redis_client, 
                    factory_name='pharma-ng', 
                    camera_id=camera_id, 
                    timestamp=time_string, 
                    frame=frame
                    )

                # # for debug
                # print(key)
                # cv2.imwrite(key+'.jpg', frame)

                # Send key reference to RabbitMQ for detection service
                # send_to_detection_queue(frame_reference, timestamp)

                last_time = time_string


camera_links = ["rtsp://admin:aci54321@192.168.12.53:554/cam/realmonitor?channel=2&subtype=0"]



import redis

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

frame_store_loop_single_camera(camera_links[0], 0, r)
