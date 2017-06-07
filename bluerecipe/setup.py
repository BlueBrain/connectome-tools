#!/usr/bin/env python
""" bluerecipe setup """

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup # pylint: disable=F0401,E0611

import pip
from pip.req import parse_requirements
from optparse import Option

from bluerecipe.version import __version__


def parse_reqs(reqs_file):
    ''' parse the requirements '''
    options = Option('--workaround')
    options.skip_requirements_regex = None
    # Hack for old pip versions: Versions greater than 1.x
    # have a required parameter "sessions" in parse_requierements
    if pip.__version__.startswith('1.'):
        install_reqs = parse_requirements(reqs_file, options=options)
    else:
        from pip.download import PipSession  # pylint:disable=E0611
        options.isolated_mode = False
        install_reqs = parse_requirements(reqs_file,  # pylint:disable=E1123
                                          options=options,
                                          session=PipSession)
    return [str(ir.req) for ir in install_reqs]

reqs = parse_reqs('requirements.txt')

setup(
    name="bluerecipe",
    version=__version__,
    install_requires=reqs,
    packages=[
        'bluerecipe',
        'bluerecipe.strategies',
    ],
    author="Michael Reimann, Arseny V. Povolotsky",
    author_email="arseny.povolotsky@epfl.ch",
    description="bluerecipe generation",
    license="BBP-internal-confidential",
    scripts=[
        'apps/s2f-recipe',
    ],
    url="http://bluebrain.epfl.ch",
    include_package_data=True
)
