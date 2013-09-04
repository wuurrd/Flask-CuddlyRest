'''
This code is inspired by:
https://github.com/brettlangdon/mongorest
'''
from flask.ext.restful import Resource
from flask.ext.cuddlyrest.marshaller import Marshaller
from flask import request, current_app
from mongoengine.queryset import DoesNotExist
from mongoengine.errors import ValidationError, InvalidQueryError
import traceback
import functools


def catch_all(function):
    @functools.wraps(function)
    def subst(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except DoesNotExist as e:
            return 'Not Found', 404
        except InvalidQueryError as e:
            return {"error": unicode(e.message)}, 400
        except ValidationError as e:
            errors = {}
            if e.field_name:
                errors[e.field_name] = unicode(e.message)
            if e.errors:
                errors.update({k: unicode(v) for k, v in e.errors.items()})
            return {"field-errors": errors}, 400
        except Exception, e:
            return {"error": traceback.format_exc(e)}, 500
    return subst


class MongoResource(Resource):

    def __init__(self, document):
        super(MongoResource, self).__init__()
        self.document = document

    def mediatypes(self):
        '''
        Flask-Restful seems to be buggy, if this method does not
        exist, it can not be plugged in by the API class, feel free to make
        a better fix if you find one
        '''
        return ['application/json']

    def options(self, *args, **kwargs):
        '''
        Restangular, and angular.js need an OPTIONS method
        '''
        resp = current_app.make_default_options_response()
        return {}, resp.status, resp.headers

    def get_filter_args(self):
        '''
        Any request arguments given will be passed directly to the mongorest
        filter, except for limit and order_by

        For None fields just use fieldname=  (with no value)
        This allows us to query embedded documents via e.g.:
        embeddedname__embeddedfieldname

        See the :mongoengine.queryset documentation for more complex examples.
        '''
        args = dict([(k, v[0] or None) for k, v in request.args.viewitems()])
        limit = args.pop('limit', None)
        if limit:
            limit = int(limit)
        skip = args.pop('skip', None)
        if skip:
            skip = int(skip)
        order = args.pop('order_by', None)
        return args, skip, limit, order


class ListMongoResource(MongoResource):
    '''
    All /basename/ requests will hit this resource.

    In general we support:
        - GET /: List all of this resource.
        - POST /: Add a new one of this resource.
    '''
    @catch_all
    def post(self):
        '''
        Add a new document
        '''
        doc = self.document()
        Marshaller(doc).loads(request.json)
        doc.save()
        return Marshaller(doc).dumps(), 201

    @catch_all
    def get(self):
        filter_args, skip, limit, order = self.get_filter_args()
        docs = self.document.objects.filter(**filter_args)
        if order:
            docs = docs.order_by(order)
        if limit:
            if not skip:
                skip = 0
            docs = docs[skip: skip + limit]
        return [Marshaller(doc).dumps() for doc in docs], 200


class SingleMongoResource(MongoResource):
    '''
    All /basename/:pk requests will hit this resource.

    In general we support:
        - GET /:pk : Show a single resource
        - DELETE /:pk : Delete this resource
        - PATCH /:pk : Do a partial update on this resource
    '''
    @catch_all
    def delete(self, doc_id):
        doc = self.document.objects.get(pk=doc_id)
        doc.delete()
        return 'Deleted', 200

    @catch_all
    def get(self, doc_id):
        doc = self.document.objects.get(pk=doc_id)
        return Marshaller(doc).dumps(), 200

    @catch_all
    def put(self, doc_id):
        doc = self.document.objects.get(pk=doc_id)
        Marshaller(doc).loads(request.json)
        doc.save()
        return self.get(doc_id)
    patch = put
