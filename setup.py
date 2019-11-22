import os
import re
import sys

from setuptools import setup

if sys.version_info >= (3, 0):
    README = open(os.path.join(os.path.dirname(__file__), 'README.md'), encoding='utf-8').read()
else:
    README = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()

reqs = ['boto3>=1.10.0', ]

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))


def get_version(*file_paths):
    """Retrieves the version from djangocms_spa/__init__.py"""
    filename = os.path.join(os.path.dirname(__file__), *file_paths)
    version_file = open(filename).read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError('Unable to find version string.')


setup(
    name='django-scarface',
    version=get_version("scarface", "__init__.py"),
    packages=['scarface'],
    include_package_data=True,
    license='MIT License',
    description='Send push notifications to mobile devices using Amazon SNS.',
    long_description=README,
    long_description_content_type='text/markdown',
    url='http://www.dreipol.ch/',
    author='dreipol GmbH',
    author_email='dev@dreipol.ch',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Framework :: Django :: 1.11',
        'Framework :: Django :: 2.0',
        'Framework :: Django :: 2.1',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    install_requires=reqs,
)
