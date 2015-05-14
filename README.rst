enum3field
===========

A Django 1.7+ model field for use with Python 2.7+ enums.

Works with any enum whose values are integers. Subclasses the IntegerField to store the enum as integers in the database. 

When creating/loading fixtures, values are serialized to dotted names, like "AnimalType.Cat" for the example below.

Installation::

	pip install -e git+https://github.com/ionata/django-enum3field.git#egg=django-enum3field

Example::

	import enum
	from enum3field import EnumField
	from django.utils.translation import ugettext_lazy as _

	class AnimalType(enum.Enum):
	    Cat = 1
	    Dog = 2
	    Turtle = 3

	@staticmethod
	def choices():  # optional, provided for translations, otherwise the choices list is create from the enum members.
	    return (
	        (AnimalType.Cat.value, _("A Cat.")),
	        (AnimalType.Dog.value, _("A Dog.")),
	        (AnimalType.Turtle.value, _("A Turtle.")),
	    )

	class Animal(models.Model):
	    animalType = EnumField(AnimalType)

Requires Python 2.7+. Not tested with Django versions prior to 1.7. Enum member changes data migrations have not tested fully.
