from mongoengine.fields import (ReferenceField, EmbeddedDocumentField,
                                BinaryField)
from mongoengine.errors import ValidationError
from datetime import datetime
from bson.objectid import ObjectId


class Marshaller(object):
    '''
    This class is responsible for loading and dropping from and to json given
    a :mongoengine.document.Document
    '''
    def __init__(self, doc):
        self.doc = doc
        self.document_cls = doc.__class__
        self.related_fields = []
        self.binary_fields = []
        self.embedded_fields = []
        for k, v in self.document_cls._fields.items():
            if isinstance(v, ReferenceField):
                self.related_fields.append(k)
            if isinstance(v, BinaryField):
                self.binary_fields.append(k)
            if isinstance(v, EmbeddedDocumentField):
                self.embedded_fields.append(k)

    def dumps(self):
        data = self.doc.to_mongo()
        for field in self.related_fields:
            data[field] = self.__class__(getattr(self.doc, field)).dumps()
        data['id'] = data['_id']
        del data['_id']
        return self.convertor(data)

    def convertor(self, value, parent=None, parent_key=None):
        '''
        Converts a BSON compatible JSON string into a REST compatible JSON
        string
        '''
        if parent_key in self.binary_fields:
            document_field = getattr(self.document_cls, parent_key)
            if hasattr(document_field, 'to_python'):
                return str(document_field.to_python(value))
        if isinstance(value, BinaryField):
            if hasattr(value, 'to_python'):
                return value.to_python()
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, ObjectId):
            return str(value)
        if isinstance(value, list):
            return [self.convertor(k) for k in value]
        if isinstance(value, dict):
            return dict((k, self.convertor(v, parent=value, parent_key=k))
                        for k, v in value.iteritems())

        return value

    def loads(self, json_data):
        for field, value in json_data.items():
            if field in self.related_fields:
                related_doc = getattr(self.document_cls,
                                      field).document_type_obj
                related_document_ref = related_doc.objects.get(pk=value)
                setattr(self.doc, field, related_document_ref)
            elif field in self.embedded_fields:
                embedded_doc = getattr(self.document_cls,
                                       field).document_type_obj
                d = embedded_doc()
                if not isinstance(value, dict):
                    raise ValidationError(field_name=field,
                                          errors={field: "should be a dict"})
                self.__class__(d).loads(value)
                setattr(self.doc, field, d)
            elif isinstance(value, dict):
                #Fallback for DictField
                setattr(self.doc, field, {})
                for k, v in value.items():
                    if isinstance(v, dict):
                        related_field = getattr(self.document_cls, field)
                        embedded_doc = related_field.field.document_type_obj
                        d = embedded_doc()
                        self.__class__(d).loads(v)
                        getattr(self.doc, field)[k] = d
            elif isinstance(value, list):
                #Fallback for listfield
                setattr(self.doc, field, [])
                related_field = getattr(self.document_cls, field)
                try:
                    embedded_doc = related_field.field
                except:
                    embedded_doc = None
                for child in value:
                    if isinstance(embedded_doc, EmbeddedDocumentField):
                        d = embedded_doc.document_type_obj()
                        self.__class__(d).loads(child)
                        getattr(self.doc, field).append(d)
                    elif isinstance(embedded_doc, ReferenceField):
                        reference_doc = embedded_doc.document_type
                        d = reference_doc.objects.get(pk=child)
                        getattr(self.doc, field).append(d)
                    else:
                        getattr(self.doc, field).append(child)
            else:
                setattr(self.doc, field, value)
        return self.doc
