
# Status
- Got frame saving loop for every second for a single camera feed. Plan to use this as a celery worker to distribute the load across multiple feeds
- next is redis to dump the frames


# Workflow
- set up rstp link and getting frames per second loop [ref](#setting-up-camera-feed-loop)
- install redis in docker 


# Refs

## Setting Up Camera Feed Loop

``` python
def save_frame_loop(rtsp_link, camera_id):
    last_time = time.time()
    last_time = time.localtime(last_time)
    last_time = time.strftime("%m_%d_%Y-%H_%M_%S", last_time)
    cap = cv2.VideoCapture(rtsp_link)
    while True:
        ret, frame = cap.read()
        if ret:
            timestamp = time.time()
            struct_time = time.localtime(timestamp)
            time_string = time.strftime("%m_%d_%Y-%H_%M_%S", struct_time)
            
            if last_time != time_string:
                cv2.imwrite(f'frame_{time_string}.png', frame)
                print(time_string)
            
            last_time = time_string
            # Optionally save frame to storage and get reference
            # frame_reference = save_frame_to_storage(frame, camera_id, timestamp)
            # Send frame reference and timestamp to RabbitMQ for detection service
            # send_to_detection_queue(frame_reference, timestamp)


camera_links = ["rtsp://admin:aci54321@192.168.12.53:554/cam/realmonitor?channel=2&subtype=0"]


save_frame_loop(camera_links[0], 0)
```
