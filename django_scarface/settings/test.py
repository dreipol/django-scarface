from local import *
from os.path import join

SOUTH_TESTS_MIGRATE = False
SKIP_SOUTH_TESTS = True

INSTALLED_APPS += \
    (
        'django_jenkins',
    )

PROJECT_APPS = (
    'backend',
)

JENKINS_TASKS = (
    'django_jenkins.tasks.with_coverage',
    'django_jenkins.tasks.run_pep8',
    'django_jenkins.tasks.run_pylint',

)

PYLINT_RCFILE = join(SITE_ROOT, 'pylint.rc')
PEP8_RCFILE = join(SITE_ROOT, 'pep8.rc')