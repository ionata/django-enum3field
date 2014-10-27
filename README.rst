enum3field
===========

A Django 1.7+ model field for use with Python 3 enums.

Works with any enum whose values are integers. Subclasses the IntegerField to store the enum as integers in the database. 

When creating/loading fixtures, values are serialized to dotted names, like "AnimalType.Cat" for the example below.

A decorator is needed on Python enums in order to make them work with Django migrations, which require a deconstruct() method on the enum members.

Installation::

	pip install enum3field

Example::

	import enum
	from enum3field import EnumField, django_enum

	@django_enum
	class AnimalType(enum.Enum):
	  Cat = 1
	  Dog = 2
	  Turtle = 3

	class Animal(models.Model):
	  animalType = EnumField(AnimalType)

Requires Python 3. Not tested with Django versions prior to 1.7 but might work.
