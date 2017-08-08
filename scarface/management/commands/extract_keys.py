# coding=utf8
from optparse import make_option

__author__ = 'dreipol GmbH'

from django.core.management.base import BaseCommand, CommandError
import os
import subprocess
import re

regex = re.compile(
    u'(?P<cert>-----BEGIN CERTIFICATE-----.*-----END CERTIFICATE-----).*(?P<key>-----BEGIN (?:RSA )?PRIVATE KEY-----.*-----END (?:RSA )?PRIVATE KEY-----)',
    re.IGNORECASE | re.MULTILINE | re.UNICODE | re.DOTALL)


class Command(BaseCommand):
    help = 'Extracts the private key and ssl certificate from an APNS p12 file'

    def add_arguments(self, parser):
        parser.add_argument('-f', '--file',
                            action='store',
                            dest='file',
                            type=str,
                            help='The APNS .p12 file')
        parser.add_argument('-p', '--password',
                            action='store',
                            dest='password',
                            type=str,
                            help='The associated password',
                            )
        parser.add_argument('-e', '--encoding',
                            action='store',
                            dest='encoding',
                            type=str,
                            help='The used encoding',
                            default='utf-8'
                            )

    def handle(self, *args, **options):
        file_name = options['file']
        password = options['password']
        encoding = options.get('encoding')
        if not (file_name and password):
            raise CommandError(u'Please specify a file and a password')

        if not os.path.isfile(file_name):
            raise CommandError(u'File "%s" does not exist'.format(file_name))
        arguments = "openssl pkcs12 -nodes -in {file} -passin pass:\"{pw}\"".format(file=file_name, pw=password)
        result = subprocess.check_output(arguments, shell=True).decode(encoding=encoding)
        groups = re.search(regex, result).groupdict()
        cert_string = groups["cert"].replace("\n", "\\n")
        key_string = groups["key"].replace("\n", "\\n")
        self.stdout.write("Copy the following two lines to your settings file:\n\n")
        self.stdout.write("SCARFACE_APNS_CERTIFICATE=\"{0}\"".format(cert_string))
        self.stdout.write("SCARFACE_APNS_PRIVATE_KEY=\"{0}\"".format(key_string))