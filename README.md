Flask-CuddlyRest
===============
A framework for manipulating mongoengine collections via a CUD-ly API

It has taken inspiration from:
 - https://github.com/brettlangdon/mongorest
 - https://github.com/elasticsales/flask-mongorest
 - https://github.com/mozilla-services/cornice (for sphinx integration)

All credit goes to those projects! :)

[![Build Status](https://travis-ci.org/wuurrd/Flask-CuddlyRest.png)](https://travis-ci.org/wuurrd/Flask-CuddlyRest)

Setup
=====

``` python
from flask import Flask
from flask.ext.mongoengine import MongoEngine
from flask.ext.cuddlyrest import CuddlyRest
from flask.ext.cuddlyrest.views import Resource


app = Flask(__name__)

app.config.update(
    MONGODB_HOST = 'localhost',
    MONGODB_PORT = '27017',
    MONGODB_DB = 'mongorest_example_app',
)

db = MongoEngine(app)
api = CuddlyRest(app)

class User(db.Document):
    email = db.EmailField(unique=True, required=True)

class Content(db.EmbeddedDocument):
    text = db.StringField()

class Post(db.Document):
    title = db.StringField(max_length=120, required=True)
    author = db.ReferenceField(User)
    content = db.EmbeddedDocumentField(Content)

api.register(Post, '/posts')
```

With this app, following cURL commands could be used:
```
Create a Post:
curl -H "Content-Type: application/json" -X POST -d \
'{"title": "First post!", "author_id": "author_id_from_a_previous_api_call", "content": {"text": "this is our test post content"}}' http://0.0.0.0:5000/posts/
{
  "id": "1",
  "title": "First post!",
  "author": "author_id_from_a_previous_api_call",
  "content": {
    "text": "this is our test post content"
  }
}
```
Get a Post:
```
curl http://0.0.0.0:5000/posts/1/
{
  "id": "1",
  "title": "First post!",
  "author_id": "author_id_from_a_previous_api_call",
  "content": {
    "text": "this is our test post content"
  }
}
```
List all Posts or filter by the title:
```
curl http://0.0.0.0:5000/posts/ or curl http://0.0.0.0:5000/posts/?title__startswith=First%20post
{
  "data": [
    {
      "id": "1",
      "title": "First post!",
      "author_id": "author_id_from_a_previous_api_call",
      "content": {
        "text": "this is our test post content"
      }
    },
    ... other posts
  ]
}
```
Delete a Post:
```
curl -X DELETE http://0.0.0.0:5000/posts/1/
```

Request Params
==============

**skip** and **limit** => utilize the built-in functions of mongodb.
**order_by** => order results if this string is present in the Resource.allowed_ordering list.
