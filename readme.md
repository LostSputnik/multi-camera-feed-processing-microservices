
# Status
- Got frame saving loop for every second for a single camera feed. Plan to use this as a celery worker to distribute the load across multiple feeds
- next is redis to dump the frames


# Workflow
- set up rstp link and getting frames per second loop [ref](#setting-up-camera-feed-loop)
- install redis in docker and test connection [ref](#set-up-redis)
- write frame data to redis and retrieve-remove [ref](#store-and-retrieve-from-redis)
- send key to RabbitMQ message-queue (current)


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

## Set up Redis
> For changes, see commit '1c31883: added redis'

We have redis in a docker container. It has a volume associated with it to store the frames. The config variable allows us to namespace different services, and also for future expansion in the env section. Other than that, i have enabled snapshots every 60 seconds for persistance. 

### Store and Retrieve from Redis
The commits are there for the changes.  Mainly, the frame-store service encodes the frame into a string, and the key has metadata info for the frames. since the metedata is already in the key, we just need to store the frame. the frame-process service retrives this frame from the redis volume and decodes it.