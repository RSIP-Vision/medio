from setuptools import setup, find_packages
from medio import __version__


def readme():
    with open('README.md') as f:
        return f.read()


setup(name='medio',
      version=__version__,
      description='Medical images I/O python package',
      long_description=readme(),
      url='https://gitlab.com/rsip/medio',
      author='Jonathan Daniel',
      author_email='jonathan@rsipvision.com',
      packages=find_packages(exclude=['*.tests']),
      install_requires=[
            'itk-io',
            'itk-filtering',
            'nibabel',
            'dicom-numpy',
            'pydicom',
            'numpy'
      ],
      classifiers=[
            'Development Status :: 2 - Pre-Alpha',

            'Intended Audience :: Developers',
            'Intended Audience :: Healthcare Industry',

            'Programming Language :: Python :: 3',

            'Topic :: Scientific/Engineering :: Medical Science Apps.',
            'Topic :: Software Development :: Libraries :: Python Modules'
      ],
      zip_safe=False)
