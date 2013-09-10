"""
Code "inspired" by Cornice's (http://cornice.readthedocs.org) own sphinx
doc generator.
"""

import sys
from importlib import import_module

import docutils
from docutils import nodes, core
from docutils.parsers.rst import Directive, directives
from docutils.writers.html4css1 import Writer, HTMLTranslator
from mongoengine.base.fields import BaseField
from mongoengine.fields import StringField, EmbeddedDocumentField, \
    ReferenceField, DateTimeField
import types


class SphinxData(object):
    def __init__(self):
        self._sphinx_mapping = {}

    def add_sphinx_mapping(self, resource, *urls):
        for url in urls:
            self._sphinx_mapping[url] = resource


def convert_to_list(argument):
    """Convert a comma separated list into a list of python values"""
    if argument is None:
        return []
    else:
        return [i.strip() for i in argument.split(',')]


def convert_to_list_required(argument):
    if argument is None:
        raise ValueError('argument required but none supplied')
    return convert_to_list(argument)


def _note(*args, **kwargs):
    note = nodes.note()
    note += nodes.paragraph(*args, **kwargs)
    return note


class ServiceDirective(Directive):
    """ Service directive.

    Injects sections in the documentation about a the HTTP service cuddlyREST
    provides to a given object (MongoDB Document).

    Usage, in a sphinx documentation::

        .. cuddlyrest::
            :document: Sock # The name of the class where the mongo document
                       binding is defined.
            :url: /socks # the url on which the document object is served.
    """
    has_content = True
    option_spec = {'document': directives.unchanged_required,
                   'url': directives.uri}
    domain = 'cuddlyrest'
    doc_field_types = []

    def __init__(self, *args, **kwargs):
        super(ServiceDirective, self).__init__(*args, **kwargs)
        self.env = self.state.document.settings.env

    def run(self):
        from jinja2 import Environment, PackageLoader

        env = Environment(loader=PackageLoader(__package__))
        template = env.get_template('service_definition.rst')

        return [rst2node(template.render(self.options))]


class ObjectDirective(Directive):
    """ Object directive.

    Injects sections in the documentation about the JSON representation of
    a cuddlyREST mapped mongoDB document.

    Usage, in a sphinx documentation::

        .. cuddlyobject::
            :module: the.module.in.which.the.document.is.defined
            :document: Sock # The name of the class where the mongo document
                       binding is defined.
            :id: sock_class # the named hyperlink reference id which the
            rest of the API doc can use to reference this generated
            documentation block. This is optional: when not provided, the
            default value will be set to the document name, lower cased.
    """
    has_content = True
    option_spec = {'module': directives.path,
                   'document': directives.unchanged_required,
                   'id': directives.unchanged}
    domain = 'cuddlyrest'
    doc_field_types = []

    def __init__(self, *args, **kwargs):
        super(ObjectDirective, self).__init__(*args, **kwargs)
        self.env = self.state.document.settings.env

    def _get_module(self, name):
        try:
            return import_module(name)
        except ImportError:
            raise self.error("Couldn't import module " + name)

    def _document_member(self, name, member):

        def _add_member_note(definition, member, qualifiers, format_text):
            if not type(qualifiers) == list:
                qualifiers = [qualifiers]
            format_param = {qualifier: getattr(member, qualifier)
                            for qualifier in qualifiers
                            if hasattr(member, qualifier)
                            and getattr(member, qualifier)
                            and type(getattr(member, qualifier)) != types.FunctionType}

            if len(qualifiers) == len(format_param):
                definition += _note(text=format_text.format(**format_param))

        def _add_member_note_if(definition, member, qualifier, text):
            if getattr(member, qualifier, False):
                definition += _note(text=text)

        node = nodes.definition_list_item()
        node += nodes.term(text=name)

        definition = nodes.definition()

        if member.help_text and len(member.help_text):
            definition += rst2node(member.help_text)

        if isinstance(member, StringField):
            node += nodes.classifier(text="String")
        elif isinstance(member, EmbeddedDocumentField):
            node += nodes.classifier(text="JSON object")
            doctype = member.document_type.__name__
            definition += rst2node("This member is an object of type "
                                   "`{}`".format(doctype))
            # definition += nodes.paragraph(self._document_class(member.document_type)
        elif isinstance(member, ReferenceField):
            node += nodes.classifier(text="String containing a "
                                     "MongoDB ObjectID")
        elif isinstance(member, DateTimeField):
            node += nodes.classifier(text="String containing a Date/Time")

        _add_member_note(definition,
                         member, 'min_length',
                         "The minimum length for this "
                         "member is {min_length} characters.")

        _add_member_note(definition,
                         member, 'max_length',
                         "The maximum length for this "
                         "member is {max_length} characters.")

        _add_member_note(definition,
                         member, 'choices',
                         "Valid values for this member are {choices}.")

        _add_member_note(definition,
                         member, 'default',
                         "The default value for this "
                         "member is {default!r}.")

        _add_member_note_if(definition,
                            member, 'required',
                            "This member is required for the creation "
                            "of a new object.")

        _add_member_note_if(definition,
                            member, 'unique',
                            "Values for this member must be unique to all "
                            "objects.")

        node += definition

        return node

    def run(self):

        # import the modules, which will populate the SERVICES variable.

        module = self._get_module(self.options.get('module'))
        klass = getattr(module, self.options.get('document'))

        result = []

        # section_id = self.options.get('id', klass_name)

        result.append(rst2node("**{} "
                               "JSON object**".format(klass.__name__)))

        klass_doc = klass.__doc__
        if klass_doc and len(klass_doc):
            result.append(rst2node(klass_doc))

        if len(klass.__dict__):
            result.append(rst2node("*Members documentation:*"))
            members_list = nodes.definition_list()
            for name, member in klass.__dict__.items():
                if isinstance(member, BaseField):
                    members_list += self._document_member(name, member)
            result.append(members_list)

        return result


def trim(docstring):
    """
    Remove the tabs to spaces, and remove the extra spaces / tabs that are in
    front of the text in docstrings.

    Implementation taken from http://www.python.org/dev/peps/pep-0257/
    """
    if not docstring:
        return ''
    # Convert tabs to spaces (following the normal Python rules)
    # and split into a list of lines:
    lines = docstring.expandtabs().splitlines()
    # Determine minimum indentation (first line doesn't count):
    indent = sys.maxint
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))
    # Remove indentation (first line is special):
    trimmed = [lines[0].strip()]
    if indent < sys.maxint:
        for line in lines[1:]:
            trimmed.append(line[indent:].rstrip())
    # Strip off trailing and leading blank lines:
    while trimmed and not trimmed[-1]:
        trimmed.pop()
    while trimmed and not trimmed[0]:
        trimmed.pop(0)
    # Return a single string:
    res = '\n'.join(trimmed)
    if not isinstance(res, unicode):
        res = res.decode('utf8')
    return res


class _HTMLFragmentTranslator(HTMLTranslator):
    def __init__(self, document):
        HTMLTranslator.__init__(self, document)
        self.head_prefix = ['', '', '', '', '']
        self.body_prefix = []
        self.body_suffix = []
        self.stylesheet = []

    def astext(self):
        return ''.join(self.body)


class _FragmentWriter(Writer):
    translator_class = _HTMLFragmentTranslator

    def apply_template(self):
        subs = self.interpolation_dict()
        return subs['body']


def rst2html(data):
    """Converts a reStructuredText into its HTML
    """
    if not data:
        return ''
    return core.publish_string(data, writer=_FragmentWriter())


class Env(object):
    temp_data = {}
    docname = ''


def rst2node(data):
    """Converts a reStructuredText into its node
    """
    if not data:
        return
    parser = docutils.parsers.rst.Parser()
    document = docutils.utils.new_document('<>')
    document.settings = docutils.frontend.OptionParser().get_default_values()
    document.settings.tab_width = 4
    document.settings.pep_references = False
    document.settings.rfc_references = False
    document.settings.env = Env()
    parser.parse(data, document)
    if len(document.children) == 1:
        return document.children[0]
    else:
        par = docutils.nodes.paragraph()
        for child in document.children:
            par += child
        return par


def setup(app):
    """Hook the directives when Sphinx ask for it."""
    app.add_directive('cuddlyobject', ObjectDirective)
    app.add_directive('cuddlyrest', ServiceDirective)
