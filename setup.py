import os

from setuptools import setup

README = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()

reqs = ['boto>=2.34.0', ]

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-scarface',
    version='3.0-alpha-7',
    packages=['scarface'],
    include_package_data=True,
    license='MIT License',
    description='Send push notifications to mobile devices using Amazon SNS.',
    long_description=README,
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
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    install_requires=reqs,
)
