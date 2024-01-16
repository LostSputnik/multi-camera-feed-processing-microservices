
# Status
- Got frame saving loop for every second for a single camera feed. Plan to use this as a celery worker to distribute the load across multiple feeds
- next is redis to dump the frames


# Workflow
- set up rstp link and getting frames per second loop [ref](#setting-up-camera-feed-loop)
- install redis in docker and test connection [ref](#set-up-redis)
- write frame data to redis and retrieve-remove [ref](#store-and-retrieve-from-redis)
- send key to RabbitMQ message-queue [ref](#connecting-to-rabbitmq-and-publish-keys)
- consume keys from message queue and read frames [ref](#consuming-messages-on-rabbitmq)
- scaling with Celery workers (current)

# To Dos
- [ ] Memory cap & management for redis
- [ ] Memory cap & management for rabbitMQ
- [ ] Update redis and rabbitMQ connection string hosts (currently set as localhost, which works, but we want it to be able to properly connect to the redis/rmq service)


# KillSwitch
```
docker compose --env-file ./config.env up -d
```

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


## Setting up RabbitMQ

### Adding RabbitMQ to system

1. First, lets set up our docker container. Going to use compose for this.

```
services:
  rabbitmq:
    image: rabbitmq:3-management-alpine
    restart: unless-stopped
    ports:
      - '5672:5672'  # AMQP protocol port
      - '15672:15672'  # Management UI port
    volumes:
      - rabbitmq-data:/var/lib/rabbitmq

volumes:
  rabbitmq-data:
    driver: local
```


I am using the management tag as it comes with the web UI and the alpine image since it is lightweight and sufficient for what we need. 
Next, we run our killswitch to up the containers.

### Connecting to rabbitMQ and publish keys
We connect using Pika, a RabbitMQ client for python

```
pip install pika
```

Now, we use pika to send messages to the queue. 
Here is an example function to send the key strings.

```python
import pika 

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
```

Then, we use this function in our frame capture loop to send the frame keys after storing the frames in redis.

```
send_key_to_queue('localhost', 'frame_queue', key)
```
Now, we need to consume these keys on the processing service.


### Consuming messages on RabbitMQ

The consumer will listen to the RabbitMQ queue, receive messages (frame keys), and then process these frames accordingly. Here's the code to receive the frames on the consumer service.

```python
import pika

def frame_process_callback(ch, method, properties, body):
    frame_key = body.decode()
    print(f'Received: {frame_key}')

    # retrive frame from redis using key
    frame = retrieve_frame_from_redis(redis_client, frame_key)

    if frame is not None:
        cv2.imwrite(frame_key+'.jpg', frame)
        
        # # not needed to explicitly delete as we use getdel when retrieving
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
```

Now, we can start the consumer with:
```python
# Assuming Redis client is already set up as 'redis_client'
start_frame_processing_consumer('localhost', 'frame_queue')
```

When we run this script, it will start listening for messages on the specified RabbitMQ queue. Each time it receives a message, it will call frame_process_callback, which retrieves and processes the frame from Redis using the key received in the message.

Some notes on this code:
- First, the prefetch count in ```channel.basic_qos(prefetch_count=1)``` determines how many messages to consume. Since we plan to process frames one by one, and have it horizontally scale with Celery workers, I set it to 1. Otherwise, a single worker will consume all the frames and process syncronously, and while other workers are waiting to consume from the queue. I need to do some more thinking on this, as to how and where better to scale from.
- Also, the position of ```channel.basic_qos(prefetch_count=1)``` matters as it must be declared before ```basic_consume``` to be effective.

- Second, on the callback, we are acknowledging the messages. Going back to the scaling topic, I will need to check whether simulanous workers receive same key before ack and such! Scaling is next up! 

# Links Dump

- [Using Redis with docker and docker-compose for local development a step-by-step tutorial](https://geshan.com.np/blog/2022/01/redis-docker/)
- [HOW TO SET UP RABBITMQ WITH DOCKER COMPOSE](https://x-team.com/blog/set-up-rabbitmq-with-docker-compose/)
- [RabbitMQ Tutorials](https://www.rabbitmq.com/tutorials/tutorial-one-python.html)