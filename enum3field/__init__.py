# A Django model field for use with Python 3 enums.
#
# Works with any enum whose values are integers. Subclasses the IntegerField
# to store the enum as integers in the database. Serializes to dotted names
# (e.g. AnimalType.Cat in the example below).
#
# Example:
#
# import enum
# from enum3field import EnumField
#
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

    # string (serialization) => enum member
    if isinstance(value, str):
      # String values must look like EnumName.MemberName. First strip
      # the "EnumName." prefix if it exists.
      prefix = self.enum_class.__name__ + "."
      if value.startswith(prefix):
        value = value[len(prefix):]

      # Now try a member lookup by name.
      try:
        return self.enum_class[value]
      except KeyError:
        raise exceptions.ValidationError(
          "'%s' must be the name of a member of %s." % (value, self.enum_class),
          code='invalid',
          params={'value': value},
          )

    # integer (db) => enum member
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
