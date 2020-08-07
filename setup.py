#!/usr/bin/env python
# pylint: disable=missing-docstring
import sys

from setuptools import find_packages, setup

from connectome_tools.version import __version__

if sys.version_info < (3, 6):
    sys.exit("Sorry, Python < 3.6 is not supported")

# read the contents of the README file
with open("README.rst", encoding="utf-8") as f:
    README = f.read()

setup(
    name="connectome-tools",
    author="BlueBrain NSE",
    author_email="bbp-ou-nse@groupes.epfl.ch",
    version=__version__,
    description="Connectome statistics; S2F recipe generation",
    long_description=README,
    long_description_content_type="text/x-rst",
    url="https://bbpteam.epfl.ch/documentation/projects/connectome-tools",
    project_urls={
        "Tracker": "https://bbpteam.epfl.ch/project/issues/projects/NSETM/issues",
        "Source": "ssh://bbpcode.epfl.ch/nse/connectome-tools",
    },
    license="BBP-internal-confidential",
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
    python_requires=">=3.6",
    extras_require={"docs": ["sphinx", "sphinx-bluebrain-theme"]},
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
    scripts=[
        "apps/connectome-stats",
        "apps/s2f-recipe",
    ],
)
