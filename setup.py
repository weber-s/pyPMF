from setuptools import setup
from os import path

VERSION = '0.1.3'

PACKAGES = [
        'pyPMF',
        ]

# read the contents of your README file
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='pyPMF',
    version=VERSION,
    packages=PACKAGES,
    include_package_data=True,    # include everything in source control
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/weber-s/pyPMF',
    install_requires=['pandas', 'xlrd<2', 'matplotlib', 'seaborn'],
    python_requires='>=3',
    author='Samuël Weber',
    author_email='samuel.weber@univ-grenoble-alpes.fr',
    project_urls={
        'Documentation': 'https://pypmf.readthedocs.io',
        'Source': 'https://github.com/weber-s/pyPMF',
        },
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Atmospheric Science',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3',
        ],
    )
