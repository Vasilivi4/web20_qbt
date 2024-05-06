from mongoengine import Document, StringField, BooleanField


class Contact(Document):
    full_name = StringField(required=True)
    email = StringField(required=True)
    phone_number = StringField(required=True)
    preferred_contact_method = StringField(choices=["SMS", "Email"], default="Email")
    is_message_sent = BooleanField(default=False)
