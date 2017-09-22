#!/usr/bin/env python
# pylint: disable=missing-docstring

from setuptools import setup

from connectome_tools.version import __version__


setup(
    name="connectome_tools",
    version=__version__,
    install_requires=[
        'click>=6.7',
        'equation>=1.2',
        'lxml>=3.3',
        'bluepy>=0.11,<0.12',
    ],
    packages=[
        'connectome_tools',
        'connectome_tools.s2f_recipe',
    ],
    author="Michael Reimann, Arseny V. Povolotsky",
    author_email="arseny.povolotsky@epfl.ch",
    description="Connectome statistics; S2F recipe generation",
    license="BBP-internal-confidential",
    scripts=[
        'apps/connectome-stats',
        'apps/s2f-recipe',
    ],
    url="https://bbpteam.epfl.ch/project/issues/projects/NSETM/issues",
    download_url="ssh://bbpcode.epfl.ch/nse/connectome-tools",
    include_package_data=True
)