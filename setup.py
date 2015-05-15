# Note to self: To upload a new version to PyPI, run:
# python3 setup.py sdist upload

from setuptools import setup, find_packages
import sys

install_requires = []
if sys.version_info[0] < 3:
    install_requires = [
        'enum34',
    ]

setup(
    name='enum3field',
    version='0.1.2',
    author=u'Joshua Tauberer',
    author_email=u'jt@occams.info',
    packages=find_packages(),
    url='https://github.com/ionata/django-enum3field',
    license='CC0 (copyright waived)',
    description='A Django 1.7+ model field for use with Python enums.',
    long_description=open("README.rst").read(),
    keywords="Django enum field",
    install_requires=install_requires,
)
