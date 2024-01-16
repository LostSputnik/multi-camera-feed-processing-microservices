import cv2
import numpy as np
import base64

import pika

# redis stuff

def encode_frame_to_string(frame):
    # Compress the frame using imencode. '.jpg' specifies the compression algorithm
    ret, buffer = cv2.imencode('.jpg', frame)
    if ret:
        return base64.b64encode(buffer).decode('utf-8')
    return None

def store_frame_to_redis(redis_client, factory_name, camera_id, timestamp, frame):
    key = f"frame:{factory_name}:{camera_id}:{timestamp}"
    frame_string = encode_frame_to_string(frame)

    redis_client.set(key, frame_string)

    return key

    # Set a TTL for the hash (e.g., 60 seconds)
    # redis_client.expire(key, 60)

# rabbitmq stuff 

def send_key_to_queue(rabbitmq_host, queue_name, frame_key):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
    channel = connection.channel()

    channel.queue_declare(queue=queue_name, durable=True)

    channel.basic_publish(exchange='',
                          routing_key=queue_name,
                          body=frame_key,
                          properties=pika.BasicProperties(
                              delivery_mode=2
                          ))

    connection.close()