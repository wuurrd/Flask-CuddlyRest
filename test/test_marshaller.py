from mongoengine.errors import ValidationError
import unittest2
from contextlib import contextmanager
from mongoengine import Document, StringField, DictField

from flask.ext.cuddlyrest.marshaller import Marshaller


class EmptyDoc(Document):
    pass
#__all__ = ['StringField',  'URLField',  'EmailField',  'IntField',  'LongField',
#           'FloatField',  'DecimalField',  'BooleanField',  'DateTimeField',
#           'ComplexDateTimeField',  'EmbeddedDocumentField', 'ObjectIdField',
#           'GenericEmbeddedDocumentField',  'DynamicField',  'ListField',
#           'SortedListField',  'DictField',  'MapField',  'ReferenceField',
#           'GenericReferenceField',  'BinaryField',  'GridFSError',
#           'GridFSProxy',  'FileField',  'ImageGridFsProxy',
#           'ImproperlyConfigured',  'ImageField',  'GeoPointField', 'PointField',
#           'LineStringField', 'PolygonField', 'SequenceField',  'UUIDField']


class BaseFieldMarshallTest(object):

    missing_default = None

    @classmethod
    def setUpClass(cls):
        class OptionalDoc(Document):
            test_field = cls.field_type(required=False)

        class RequiredDoc(Document):
            test_field = cls.field_type(required=True)

        cls.OptionalDoc = OptionalDoc
        cls.RequiredDoc = RequiredDoc

    @contextmanager
    def noop_context(self):
        yield

    def raises_validation_error(self):
        return self.assertRaises(ValidationError)

    def do_test(self, doc_cls, load, expected, validate_context):
        doc = doc_cls()

        m = Marshaller(doc)
        m.loads(load)

        self.assertEqual(doc.test_field, expected)
        with validate_context():
            doc.validate()

    def test_optional_missing(self):
        self.do_test(
            self.OptionalDoc,
            {},
            self.missing_default,
            self.noop_context,
        )

    def test_optional_with_none(self):
        self.do_test(
            self.OptionalDoc,
            {'test_field': None},
            self.missing_default,
            self.noop_context,
        )

    def test_required_missing(self):
        self.do_test(
            self.RequiredDoc,
            {},
            self.missing_default,
            self.raises_validation_error,
        )

    def test_required_with_none(self):
        self.do_test(
            self.RequiredDoc,
            {'test_field': None},
            None,
            self.raises_validation_error,
        )

    def _test_with_value(self, doc_cls, test_value, validate_context):
        self.do_test(
            doc_cls,
            {'test_field': test_value},
            test_value,
            validate_context,
        )

    def test_optional_valid_values(self):
        for value in self.valid_values:
            self._test_with_value(self.OptionalDoc, value, self.noop_context)

    def test_optional_invalid_values(self):
        for value in self.invalid_values:
            self._test_with_value(
                self.OptionalDoc,
                value,
                self.raises_validation_error
            )

    def test_required_valid_values(self):
        for value in self.valid_values:
            self._test_with_value(self.RequiredDoc, value, self.noop_context)

    def test_required_invalid_values(self):
        for value in self.invalid_values:
            self._test_with_value(
                self.RequiredDoc,
                value,
                self.raises_validation_error
            )


class StringFieldMarshallTest(BaseFieldMarshallTest, unittest2.TestCase):
    field_type = StringField
    valid_values = ['abcd']
    invalid_values = [2]


class DictStringFieldMarshallTest(BaseFieldMarshallTest, unittest2.TestCase):

    @staticmethod
    def field_type(**kwargs):
        return DictField(StringField, StringField, **kwargs)

    valid_values = [{}, {'abc': 'def'}]
    invalid_values = [{'abc': 2}]
    missing_default = {}


class TestMarshaller(unittest2.TestCase):

    class TestDoc(Document):
        test = StringField()

    @contextmanager
    def marshaller(self, doc):
        yield Marshaller(doc)

    def test_empty(self):
        doc = self.TestDoc()

        with self.marshaller(doc) as m:
            m.loads({})

        self.assertEqual(doc.test, None)

    def test_string(self):
        doc = self.TestDoc()
        test_string = 'yay'
        with self.marshaller(doc) as m:
            m.loads({'test': test_string})

        self.assertEqual(doc.test, test_string)

    def test_extra(self):
        doc = self.TestDoc()

        with self.assertRaises(AttributeError):
            with self.marshaller(doc) as m:
                m.loads({'foo': 'bar'})

        self.assertEqual(doc.test, None)
