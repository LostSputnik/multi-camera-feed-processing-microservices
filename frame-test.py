from celery import Celery
import cv2
import time

app = Celery('frame_processing_tasks', broker='pyamqp://guest@localhost//')

@app.task
def process_frame(rtsp_link, camera_id):
    cap = cv2.VideoCapture(rtsp_link)
    while True:
        ret, frame = cap.read()
        if ret:
            timestamp = time.time()
            print(time.strftime("%m_%d_%Y-%H_%M_%S",timestamp))
            cv2.imwrite(f'frame_{timestamp}.png', frame)
            # Optionally save frame to storage and get reference
            # frame_reference = save_frame_to_storage(frame, camera_id, timestamp)
            # Send frame reference and timestamp to RabbitMQ for detection service
            # send_to_detection_queue(frame_reference, timestamp)
        time.sleep(.1)  # Control frame rate

# Example: Add your camera RTSP links here
camera_links = ["rtsp://admin:aci54321@192.168.12.53:554/cam/realmonitor?channel=2&subtype=0"]
# camera_links = ["rtsp://admin:misaci1234@192.168.18.41:554/cam/realmonitor?channel=2&subtype=0"]

# Send tasks to Celery
for idx, link in enumerate(camera_links):
    process_frame.delay(link, idx)
