#!/usr/bin/env python
# pylint: disable=missing-docstring
import sys

from setuptools import find_packages, setup

from connectome_tools.version import __version__

if sys.version_info < (3, 8):
    sys.exit("Sorry, Python < 3.8 is not supported")

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
        "Source": "https://bbpgitlab.epfl.ch/nse/connectome-tools/",
    },
    license="BBP-internal-confidential",
    install_requires=[
        "click>=7.0,<9.0",
        "equation>=1.2",
        "joblib>=1.0.1",
        "lxml>=3.3",
        "numpy>=1.9",
        "pandas>=1.0.0",
        "psutil>=5.7.2",
        "pyyaml>=5.3.1",
        "submitit>=1.3.3",
        "bluepy>=2.3,<3.0",
        "morphio>=3.0.1,<4.0.0",
        "voxcell>=3.0,<4.0",
    ],
    packages=find_packages(),
    python_requires=">=3.8",
    extras_require={"docs": ["sphinx", "sphinx-bluebrain-theme"]},
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
    entry_points={
        "console_scripts": [
            "connectome-stats=connectome_tools.apps.connectome_stats:app",
            "s2f-recipe=connectome_tools.apps.s2f_recipe:app",
            "s2f-recipe-merge=connectome_tools.apps.s2f_recipe_merge:cli",
        ],
    },
)
