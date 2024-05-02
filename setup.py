#!/usr/bin/env python

from setuptools import find_packages, setup

from hyperion import _LIBRARY_VERSION

setup(
    name="HyperionAPI",
    version=_LIBRARY_VERSION,
    description="Public API for Hyperion Instruments from Micron Optics, Inc.",
    author="Dustin W. Carr",
    author_email="dcarr@micronoptics.com",
    packages=find_packages(include=["HyperionAPI*"]),
    install_requires=[
        "numpy",
        "datetime",
        # other dependencies
    ],
)
