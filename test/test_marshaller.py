from mongoengine.errors import ValidationError
import unittest2
from contextlib import contextmanager
from mongoengine import (
    EmbeddedDocument, Document, EmbeddedDocumentField, StringField, DictField)

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
    valid_optional_values = []
    valid_required_values = []

    @classmethod
    def setUpClass(cls):
        class OptionalFieldDoc(Document):
            test_field = cls.field_type(required=False)

        class RequiredFieldDoc(Document):
            test_field = cls.field_type(required=True)

        class EmbeddedOptionalFieldDoc(EmbeddedDocument):
            test_field = cls.field_type(required=False)

        class EmbeddedRequiredFieldDoc(EmbeddedDocument):
            test_field = cls.field_type(required=True)

        class OptionalEmbeddedOptionalFieldDoc(Document):
            test_doc = EmbeddedDocumentField(
                EmbeddedOptionalFieldDoc, required=False)

        class OptionalEmbeddedRequiredFieldDoc(Document):
            test_doc = EmbeddedDocumentField(
                EmbeddedRequiredFieldDoc, required=False)

        class RequiredEmbeddedOptionalFieldDoc(Document):
            test_doc = EmbeddedDocumentField(
                EmbeddedOptionalFieldDoc, required=True)

        class RequiredEmbeddedRequiredFieldDoc(Document):
            test_doc = EmbeddedDocumentField(
                EmbeddedRequiredFieldDoc, required=True)

        cls.OptionalFieldDoc = OptionalFieldDoc
        cls.RequiredFieldDoc = RequiredFieldDoc
        cls.embed_docs = {
            False: {
                False: OptionalEmbeddedOptionalFieldDoc,
                True: OptionalEmbeddedRequiredFieldDoc,
            },
            True: {
                False: RequiredEmbeddedOptionalFieldDoc,
                True: RequiredEmbeddedRequiredFieldDoc,
            }
        }

    @contextmanager
    def noop_context(self):
        yield

    def raises_validation_error(self):
        return self.assertRaises(ValidationError)

    def _do_test(self, doc_cls, load, expected, validate_context, check):
        doc = doc_cls()

        m = Marshaller(doc)
        m.loads(load)

        check(doc)
        with validate_context():
            doc.validate()

    def do_test(self, doc_cls, load, expected, validate_context):
        def check(doc):
            self.assertEqual(doc.test_field, expected)
        return self._do_test(
            doc_cls,
            load,
            expected,
            validate_context,
            check)

    def test_optional_missing(self):
        self.do_test(
            self.OptionalFieldDoc,
            {},
            self.missing_default,
            self.noop_context,
        )

    def test_optional_with_none(self):
        self.do_test(
            self.OptionalFieldDoc,
            {'test_field': None},
            self.missing_default,
            self.noop_context,
        )

    def test_required_missing(self):
        self.do_test(
            self.RequiredFieldDoc,
            {},
            self.missing_default,
            self.raises_validation_error,
        )

    def test_required_with_none(self):
        self.do_test(
            self.RequiredFieldDoc,
            {'test_field': None},
            self.missing_default,
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
        for value in self.valid_values + self.valid_optional_values:
            self._test_with_value(self.OptionalFieldDoc, value, self.noop_context)

    def test_optional_invalid_values(self):
        for value in self.invalid_values:
            self._test_with_value(
                self.OptionalFieldDoc,
                value,
                self.raises_validation_error
            )

    def test_required_valid_values(self):
        for value in self.valid_values + self.valid_required_values:
            self._test_with_value(
                self.RequiredFieldDoc,
                value,
                self.noop_context)

    def test_required_invalid_values(self):
        for value in self.invalid_values:
            self._test_with_value(
                self.RequiredFieldDoc,
                value,
                self.raises_validation_error
            )

    def _test_embeded_with_value(self, test_value, validate_context):
        for required_doc in (False, True):
            for required_field in (False, True):
                doc_cls = self.embed_docs[required_doc][required_field]
                self._do_test(
                    doc_cls,
                    {},
                    None,
                    self.noop_context if not required_doc else self.raises_validation_error,
                    lambda d: self.assertIsNone(d.test_doc)
                )

                if not required_doc:
                    self._do_test(
                        doc_cls,
                        {'test_doc': None},
                        None,
                        self.noop_context,
                        lambda d: self.assertIsNone(d.test_doc)
                    )

                self._do_test(
                    doc_cls,
                    {'test_doc': {'test_field': None}},
                    None,
                    self.noop_context if not required_field else self.raises_validation_error,
                    lambda d: self.assertIsNotNone(d.test_doc) and self.assertNone(d.test_doc.test_field)
                )

                self._do_test(
                    doc_cls,
                    {'test_doc': {'test_field': test_value}},
                    test_value,
                    validate_context,
                    lambda d: self.assertIsNotNone(d.test_doc) and self.assertEqual(d.test_doc.test_field, test_value)
                )

    def test_optional_embed_valid_values(self):
        for value in self.valid_values:
            self._test_embeded_with_value(value, self.noop_context)

    def test_optional_embed_invalid_values(self):
        for value in self.invalid_values:
            self._test_embeded_with_value(
                value,
                self.raises_validation_error
            )

    def test_required_embed_valid_values(self):
        for value in self.valid_values + self.valid_required_values:
            self._test_embeded_with_value(
                value,
                self.noop_context)

    def test_required_embed_invalid_values(self):
        for value in self.invalid_values:
            self._test_embeded_with_value(
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
        return DictField(StringField, StringField(), **kwargs)

    valid_values = [{'abc': 'def'}]
    valid_optional_values = [{}]
    invalid_values = [{'abc': 2}]
    missing_default = {}

