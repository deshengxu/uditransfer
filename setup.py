#!/usr/bin/env python

# ...

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
from uditransfer import __version__

setup(name='ca.py',
      version=__version__,
      description='uditransfer.py: copy HL7 message and acknowledgements',
      author='Desheng Xu',
      author_email='dxu@ptc.com',
      maintainer='Desheng Xu',
      maintainer_email='dxu@ptc.com',
      url=' ',
      packages=['uditransfer'],
      long_description="A python tool copy HL7 and ACKs safely.",
      license="PTC Only",
      platforms=["any"],
      #install_requires=['matplotlib','pandas'],
      )
