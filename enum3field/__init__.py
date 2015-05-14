# A Django model field for use with Python 3 enums.
#
# Works with any enum whose values are integers. Subclasses the IntegerField
# to store the enum as integers in the database. Serializes to dotted names
# (e.g. AnimalType.Cat in the example below).
#
# A decorator is needed on Python enums in order to make them work with
# Django migrations, which require a deconstruct() method on the enum
# members.
#
# Example:
#
# import enum
# from enum3field import EnumField, django_enum
#
# @django_enum
# class AnimalType(enum.Enum):
#   Cat = 1
#   Dog = 2
#   Turtle = 3
#
# class Animal(models.Model):
#   animalType = EnumField(AnimalType)
#
#####################################################
from __future__ import absolute_import, unicode_literals

from django import forms
from django.core import exceptions
from django.core import validators
from django.core.exceptions import ValidationError
from django.db import models
from django.forms.widgets import NumberInput
from django.utils import formats
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
import enum
from django.utils.six import with_metaclass
from django.utils.deconstruct import deconstructible
import types


class EnumFormField(forms.TypedChoiceField):
    def __init__(self, *args, **kwargs):
        self.coerce = kwargs.pop('coerce', lambda val: self.default_coerce)
        self.empty_value = kwargs.pop('empty_value', '')
        super(EnumFormField, self).__init__(*args, **kwargs)

    def default_coerce(self, value):
        return self.enum_class(value)

    def prepare_value(self, value):
        # return enum member.value
        return value.value


class EnumField(with_metaclass(models.SubfieldBase, models.IntegerField)):
    """A Django model field for use with Python 3 enums. Usage: fieldname = EnumField(enum_class, ....)"""

    description = _("Enum")

    default_error_messages = {
        'invalid': _("'%(value)s' value must be an enum member."),
    }

    def __init__(self, enum_class, *args, **kwargs):
        if not issubclass(enum_class, enum.Enum) or issubclass(enum_class, enum.IntEnum):
            raise ValueError("enum_class must be of the enum.Enum type and cannot be enum.IntEnum due to a serialisation issue.")

        if not all([isinstance(member.value, int) for member in enum_class]):
            raise ValueError("enum_class members must have numeric values.")

        self.enum_class = enum.unique(enum_class)  # ensure unique members to prevent accidental database corruption

        choices = kwargs.get('choices', None)
        if not choices:
            if hasattr(enum_class, 'choices') and callable(enum_class.choices):
                kwargs['choices'] = enum_class.choices()
            else:
                kwargs['choices'] = [(item, item.name) for item in self.enum_class]

        super(EnumField, self).__init__(*args, **kwargs)

    description = "A value of the %(enum_class) enumeration."

    def get_prep_value(self, value):
        # Normally value is an enumeration value. But when running `manage.py migrate`
        # we may get a serialized value. Use to_python to coerce to an enumeration
        # member as best as possible.
        value = self.to_python(value)

        if value is not None:
            # Validate
            if not isinstance(value, self.enum_class):
                raise exceptions.ValidationError(
                    "'%s' must be a member of %s." % (value, self.enum_class),
                    code='invalid',
                    params={'value': value},
                )

            # enum member => member.value (should be an integer)
            value = value.value

        # integer => database
        return super(EnumField, self).get_prep_value(value)

    def to_python(self, value):
        # handle None and values of the correct type already
        if value is None or isinstance(value, self.enum_class):
            return value

        # When serializing to create a fixture, the default serialization
        # is to "EnumName.MemberName". Handle that.
        prefix = self.enum_class.__name__ + "."
        if isinstance(value, (str, unicode)) and value.startswith(prefix):
            try:
                return self.enum_class[value[len(prefix):]]
            except KeyError:
                raise exceptions.ValidationError(
                    "'%s' does not refer to a member of %s." % (value, self.enum_class),
                    code='invalid',
                    params={'value': value},
                )

        # We may also get string versions of the integer form from forms,
        # and integers when querying a database.
        try:
            return self.enum_class(int(value))
        except ValueError:
            raise exceptions.ValidationError(
                "'%s' must be an integer value of %s." % (value, self.enum_class),
                code='invalid',
                params={'value': value},
            )

    def deconstruct(self):
        # Override the positional arguments info to include the enumeration class.
        name, path, args, kwargs = super(EnumField, self).deconstruct()

        default = kwargs.get('default', None)
        if default and isinstance(default, self.enum_class):
            kwargs['default'] = default.value

        choices = kwargs.get('choices', None)
        if choices:
            choices = map(lambda e: (e[0].value if isinstance(e[0], self.enum_class) else e[0], e[1]), choices)
            kwargs['choices'] = choices

        return name, path, [self.enum_class], kwargs

    @cached_property
    def validators(self):
        # IntegerField validators will not work on enum instances, and we don't need
        # any validation beyond conversion to an enum instance (which is performed
        # elsewhere), so we don't need to do any validation.
        return []

    def formfield(self, **kwargs):
        defaults = {
            'form_class': EnumFormField,
            'choices_form_class': EnumFormField,
        }
        defaults.update(kwargs)
        return super(EnumField, self).formfield(**defaults)
