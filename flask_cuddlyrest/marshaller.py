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
            if getattr(self.doc, field):
                data[field] = self.__class__(getattr(self.doc, field)).dumps()
            else:
                data[field] = None
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
        for field_name, value in json_data.items():
            field = getattr(self.document_cls, field_name)

            if field_name in self.related_fields:
                related_doc = field.document_type
                related_document_ref = related_doc.objects.get(pk=value)
                setattr(self.doc, field_name, related_document_ref)
            elif field_name in self.embedded_fields:
                embedded_doc = field.document_type

                if value is None and not field.required:
                    d = None
                elif isinstance(value, dict):
                    d = embedded_doc()
                    self.__class__(d).loads(value)
                else:
                    raise ValidationError(
                        field_name=field_name,
                        errors={field_name: "should be a dict"})

                setattr(self.doc, field_name, d)
            elif isinstance(value, dict):
                #Fallback for DictField
                dct = {}
                setattr(self.doc, field_name, dct)
                for k, v in value.items():
                    if isinstance(v, dict):
                        embedded_doc = field.field.document_type
                        d = embedded_doc()
                        self.__class__(d).loads(v)
                        dct[k] = d
                    else:
                        dct[k] = v

            elif isinstance(value, list):
                #Fallback for listfield
                setattr(self.doc, field_name, [])
                try:
                    embedded_doc = field.field
                except:
                    embedded_doc = None
                for child in value:
                    if isinstance(embedded_doc, EmbeddedDocumentField):
                        d = embedded_doc.document_type()
                        self.__class__(d).loads(child)
                        getattr(self.doc, field_name).append(d)
                    elif isinstance(embedded_doc, ReferenceField):
                        reference_doc = embedded_doc.document_type
                        d = reference_doc.objects.get(pk=child)
                        getattr(self.doc, field_name).append(d)
                    else:
                        getattr(self.doc, field_name).append(child)
            else:
                setattr(self.doc, field_name, value)
        return self.doc
