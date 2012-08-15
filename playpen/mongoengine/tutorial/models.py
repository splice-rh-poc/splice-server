from mongoengine import *

class User(Document):
    email = StringField(required=True, unique=True)
    first_name = StringField(max_length=50)
    last_name = StringField(max_length=50, unique_with="first_name")
    # Example of defining an index
    meta = {
        "indexes": [
            {"fields": ["email"], "unique": True},
            {"fields": ["first_name", "last_name"], "unique": True},
        ]
    }

class Comment(EmbeddedDocument):
    content = StringField()
    name = StringField(max_length=120)

class Post(Document):
    meta = {
            "collection": "postings", #example to change collection name
            "allow_inheritance": True,
            }
    title = StringField(max_length=120, required=True)
    author = ReferenceField(User, reverse_delete_rule=CASCADE)
    tags = ListField(StringField(max_length=30))
    comments = ListField(EmbeddedDocumentField(Comment))

class TextPost(Post):
    content = StringField()

class ImagePost(Post):
    image_path = StringField()

class LinkPost(Post):
    link_url = StringField()

