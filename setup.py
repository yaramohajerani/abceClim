import os
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
import platform


cmdclass = {}

install_requires = ['future',
                    'pandas >= 1.0.0',
                    'sqlalchemy >= 2.0.0']


readthedocs = os.environ.get('READTHEDOCS') == 'True'

if not readthedocs:
    if not platform.python_implementation() == "PyPy":
        install_requires += ['numpy >= 1.10.2']
        if ('APPVEYOR' not in os.environ) or ('TRAVIS' not in os.environ):
            install_requires += ['bokeh == 0.12.16',
                                 'tornado']


version = '0.9.7b0'


setup(name='abcEconomics',
      version=version,
      author='Davoud Taghawi-Nejad',
      author_email='Davoud@Taghawi-Nejad.de',
      description='Agent-Based Complete Economy modelling platform',
      url='https://github.com/AB-CE/abce.git',
      package_dir={'abcEconomics': 'abcEconomics',
                   'abcEconomics.agents': 'abcEconomics/agents',
                   'abcEconomics.contracts': 'abcEconomics/contracts',
                   'abcEconomics.logger': 'abcEconomics/logger',
                   'abcEconomics.scheduler': 'abcEconomics/scheduler'
                   },
      packages=['abcEconomics'],
      long_description=open('README.rst').read(),
      setup_requires=['setuptools>=18.0', 'cython'],
      install_requires=install_requires,
      include_package_data=True,
      cmdclass=cmdclass)
