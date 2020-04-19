from setuptools import setup, find_packages
from medio import __version__


with open('README.md') as f:
    long_description = f.read()


setup(name='medio',
      version=__version__,
      description='Medical images I/O python package',
      long_description=long_description,
      long_description_content_type='text/markdown',
      url='https://gitlab.com/rsip/medio',
      author='Jonathan Daniel',
      author_email='jonathan@rsipvision.com',
      keywords=['medical images', 'IO', 'itk', 'nibabel', 'pydicom'],
      packages=find_packages(exclude=['*.tests']),
      install_requires=[
            'itk-io >= 5.0.1',
            'itk-filtering >= 5.0.1',
            'nibabel >= 3.0.2',
            'dicom-numpy >= 0.3.0',
            'pydicom >= 1.4.2',
            'numpy >= 1.18.1'
      ],
      classifiers=[
            'Development Status :: 3 - Alpha',

            'Intended Audience :: Developers',
            'Intended Audience :: Healthcare Industry',

            'Topic :: Scientific/Engineering :: Medical Science Apps.',
            'Topic :: Software Development :: Libraries :: Python Modules',

            'Programming Language :: Python :: 3',
            'Operating System :: OS Independent'
      ],
      zip_safe=True)
