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

import enum

from django.core import exceptions
from django.db import models
from django.utils.functional import cached_property

def django_enum(enum):
  # In order to make the enumeration serializable for migrations, instance members
  # must have a deconstruct method. But the enum class should not have a deconstruct
  # method or else the serialization of the enum itself as the first argument to
  # EnumField will fail. To achieve this, we added a deconstruct() method to the
  # members after the enum members have been created.
  def make_deconstructor(member):
    def deconstruct():
      return (enum.__module__ + '.' + enum.__name__, [member.value], {})
    return deconstruct
  for member in enum:
    member.deconstruct = make_deconstructor(member)
  return enum

class EnumField(models.IntegerField, metaclass=models.SubfieldBase):
  """A Django model field for use with Python 3 enums. Usage: fieldname = EnumField(enum_class, ....)"""
  
  def __init__(self, enum_class, *args, **kwargs):
    if not issubclass(enum_class, enum.Enum):
      raise ValueError("enum_class argument must be a Python 3 enum.")
    self.enum_class = enum.unique(enum_class) # ensure unique members to prevent accidental database corruption
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
    if isinstance(value, str) and value.startswith(prefix):
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
    tup = super(EnumField, self).deconstruct()
    return (tup[0], tup[1], [self.enum_class], tup[3])
 
  @cached_property
  def validators(self):
    # IntegerField validators will not work on enum instances, and we don't need
    # any validation beyond conversion to an enum instance (which is performed
    # elsewhere), so we don't need to do any validation.
    return []
 
