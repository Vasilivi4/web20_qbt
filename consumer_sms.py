import pika
import json
from contact_model import Contact

connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
channel = connection.channel()

channel.queue_declare(queue="sms_queue")
channel.queue_declare(queue="email_queue")


def callback(ch, method, properties, body):
    contact_data = json.loads(body)
    contact = Contact(**contact_data)
    contact.save()
    print(f"Received and saved contact: {contact_data}")


channel.basic_consume(queue="sms_queue", on_message_callback=callback, auto_ack=True)
print("Waiting for SMS contacts...")
channel.start_consuming()
