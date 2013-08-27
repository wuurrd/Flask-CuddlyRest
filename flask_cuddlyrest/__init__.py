from bson import json_util
from flask import make_response
from flask.ext.restful import Api
from flask.ext.cuddlyrest.views import ListMongoResource, SingleMongoResource


class CuddlyRest(Api):
    def __init__(self, app):
        super(CuddlyRest, self).__init__(app=app)
        self.representation('application/json')(self.json_encode)

    def json_encode(self, data, code, headers=None):
        resp = make_response(json_util.dumps(data, indent=4), code)
        if headers:
            resp.headers.extend(headers)
        return resp

    def register(self, collection, name):
        collection_resource = SingleMongoResource(collection)
        collection_list = ListMongoResource(collection)
        self.add_resource(collection_resource, '/%s/<string:doc_id>'
                          % name,
                          endpoint=name + '_single',
                          document=collection)
        self.add_resource(collection_list, '/%s' % name,
                          endpoint=name + '_multiple',
                          document=collection)

    def run(self, *args, **kwargs):
        self.app.run(*args, **kwargs)

    def add_resource(self, resource, *urls, **kwargs):
        """Adds a resource to the api.

        :param resource: the class name of your resource
        :type resource: :class:`Resource`
        :param urls: one or more url routes to match for the resource, standard
                     flask routing rules apply.  Any url variables will be
                     passed to the resource method as args.
        :type urls: str

        :param endpoint: endpoint name (defaults to
            :meth:`Resource.__name__.lower`
            Can be used to reference this route in :class:`fields.Url` fields
        :type endpoint: str

        Additional keyword arguments not specified above will be passed as-is
        to :meth:`flask.Flask.add_url_rule`.

        Examples::

            api.add_resource(HelloWorld, '/', '/hello')
            api.add_resource(Foo, '/foo', endpoint="foo")
            api.add_resource(FooSpecial, '/special/foo', endpoint="foo")

        """
        endpoint = kwargs.pop('endpoint', None) or resource.__name__.lower()
        self.endpoints.add(endpoint)

        if endpoint in self.app.view_functions.keys():
            previous_view_class = (self.app.view_functions[endpoint]
                                   .__dict__['view_class'])

            # if you override the endpoint with a different class, avoid the
            # collision by raising an exception
            if previous_view_class != resource:
                raise ValueError(
                    'This endpoint (%s) is already set to the class %s.'
                    % (endpoint, previous_view_class.__name__))

        resource.endpoint = endpoint
        resource_func = self.output(resource.as_view(endpoint, **kwargs))

        for decorator in self.decorators:
            resource_func = decorator(resource_func)

        for url in urls:
            self.app.add_url_rule(self.prefix + url, view_func=resource_func)
