#!/usr/bin/env python
# pylint: disable=missing-docstring

from setuptools import find_packages, setup

from connectome_tools.version import __version__

setup(
    name="connectome-tools",
    version=__version__,
    install_requires=[
        "click>=7.0,<8.0",
        "equation>=1.2",
        "joblib>=0.16.0",
        "lxml>=3.3",
        "numpy>=1.9",
        "pandas>=0.17",
        "pyyaml>=5.3.1",
        "six>=1.0",
        "bluepy>=0.13.0",
        "voxcell>=2.5.6",
    ],
    packages=find_packages(),
    author="BlueBrain NSE",
    author_email="bbp-ou-nse@groupes.epfl.ch",
    description="Connectome statistics; S2F recipe generation",
    license="BBP-internal-confidential",
    scripts=[
        "apps/connectome-stats",
        "apps/s2f-recipe",
    ],
    url="https://bbpteam.epfl.ch/project/issues/projects/NSETM/issues",
    download_url="ssh://bbpcode.epfl.ch/nse/connectome-tools",
)
