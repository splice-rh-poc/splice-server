#!/usr/bin/env python

from mongoengine import *
from models import User, Post, TextPost, ImagePost, LinkPost, Comment

DATABASE_NAME="tumbleblog"
connect(DATABASE_NAME)

def cleanup():
    User.drop_collection()
    Post.drop_collection()

def populate_data():
    john = User(email='jdoe@example.com', first_name="John", last_name="Doe")
    john.save()

    post1 = TextPost(title="Fun with MongoEngine", author=john)
    post1.content = "Took a look at MongoEngine today, looks pretty cool."
    post1.tags = ['mongodb', 'mongoengine']
    post1.save()

    post2 = LinkPost(title="MongoEngine Documentation", author=john)
    post2.link_url = "http://tractiondigital.com/labs/mongoengine/docs"
    post2.tags = ["mongoengine"]
    post2.save()

def example_query():
    for post in Post.objects:
        print post.title
        print "=" * len(post.title)

        if isinstance(post, TextPost):
            print post.content

        if isinstance(post, LinkPost):
            print "Link:", post.link_url

        print

        for post in Post.objects(tags='mongodb'):
            print post.title

        num_posts = Post.objects(tags="mongodb").count()
        print "Found %d posts with tag 'mongodb'" % num_posts


if __name__ == "__main__":
    cleanup()
    populate_data()
    example_query()

