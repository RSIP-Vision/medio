from setuptools import setup, find_packages

from medio import __version__

with open('README.md') as f:
    long_description = f.read()


setup(name='medio',
      version=__version__,
      description='Medical images I/O python package',
      long_description=long_description,
      long_description_content_type='text/markdown',
      url='https://github.com/RSIP-Vision/medio',
      author='RSIP Vision',
      author_email='info@rsipvision.com',
      keywords=['medical-images', 'IO', 'itk', 'nibabel', 'pydicom', 'python'],
      packages=find_packages(exclude=['*.tests']),
      install_requires=[
            'itk >= 5.2rc2',
            'nibabel >= 3.0.2',
            'pydicom >= 2.0.0',
            'dicom-numpy >= 0.4.0',
            'numpy >= 1.18.1'
      ],
      python_requires='>=3.6',
      classifiers=[
            'Development Status :: 3 - Alpha',

            'Intended Audience :: Developers',
            'Intended Audience :: Education',
            'Intended Audience :: Healthcare Industry',
            'Intended Audience :: Science/Research',

            'Topic :: Scientific/Engineering :: Medical Science Apps.',
            'Topic :: Software Development :: Libraries :: Python Modules',

            'Programming Language :: Python',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',

            'Operating System :: OS Independent'
      ],
      license='Apache License 2.0',
      zip_safe=True)
