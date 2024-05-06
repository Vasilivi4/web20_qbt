import pika
from time import sleep
from contact_model import Contact

connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
channel = connection.channel()
channel.queue_declare(queue="contacts_queue")


def send_email_stub(contact_id):
    print(f"Sending email to contact with ID: {contact_id}")


def callback(ch, method, properties, body):
    contact_id = body.decode()
    contact = Contact.objects.get(id=contact_id)

    send_email_stub(contact_id)

    contact.message_sent = True
    contact.save()

    print(f"Email sent to contact with ID: {contact_id}")


channel.basic_consume(
    queue="contacts_queue", on_message_callback=callback, auto_ack=True
)

print("Waiting for messages...")
channel.start_consuming()
