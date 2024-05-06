import pika
import json
from faker import Faker
from contact_model import Contact

connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
channel = connection.channel()

channel.queue_declare(queue="sms_queue")
channel.queue_declare(queue="email_queue")

fake = Faker()
for _ in range(10):
    contact = {
        "full_name": fake.name(),
        "email": fake.email(),
        "phone_number": fake.phone_number(),
        "preferred_contact_method": fake.random_element(elements=("SMS", "Email")),
    }
    channel.basic_publish(
        exchange="",
        routing_key=(
            "sms_queue"
            if contact["preferred_contact_method"] == "SMS"
            else "email_queue"
        ),
        body=json.dumps(contact),
    )
    print(f"Generated and sent contact: {contact}")

connection.close()
