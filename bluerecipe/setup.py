#!/usr/bin/env python
""" bluerecipe setup """

from setuptools import setup

from bluerecipe.version import __version__


setup(
    name="bluerecipe",
    version=__version__,
    install_requires=[
        'click>=6.7',
        'equation>=1.2',
        'lxml>=3.3',
        'bluepy>=0.11,<0.12',
    ],
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
        'apps/connectome-stats',
    ],
    url="http://bluebrain.epfl.ch",
    include_package_data=True
)
