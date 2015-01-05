import os
from setuptools import setup

README = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()

reqs =['South>=0.8.4', 'boto>=2.34.0',]

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-translator',
    version='1.0',
    packages=['translator'],
    include_package_data=True,
    license='MIT License',
    description='Translator is an app for collecting translations for specified keys in django admin.',
    long_description=README,
    url='http://www.dreipol.ch/',
    author='dreipol GmbH',
    author_email='dev@dreipol.ch',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License', # example license
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    install_requires=reqs,
)