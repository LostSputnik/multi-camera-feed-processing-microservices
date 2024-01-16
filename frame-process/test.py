import cv2
import redis
import pika

from utils import retrieve_frame_from_redis

def frame_process_callback(ch, method, properties, body):
    frame_key = body.decode()
    print(f'Received: {frame_key}')

    # retrive frame from redis using key
    frame = retrieve_frame_from_redis(redis_client, frame_key)

    if frame is not None:
        cv2.imwrite(frame_key+'.jpg', frame)
        
        # # not needed as we use getdel when retrieving
        # delete_frame_from_redis(redis_client, frame_key)
    
    else:
        print('NOT FOUND - ', frame_key)

    # acknowledge the message
    ch.basic_ack(delivery_tag=method.delivery_tag)

def start_frame_processing_consumer(rabbitmq_host, queue_name):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
    channel = connection.channel()

    channel.queue_declare(queue=queue_name, durable=True)

    # set up consumer
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=queue_name, on_message_callback=frame_process_callback)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()
        

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

start_frame_processing_consumer('localhost', 'frame_queue')