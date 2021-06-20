from setuptools import setup, find_packages


def get_version(rel_path):
    with open(rel_path, 'r') as fp:
        for line in fp:
            if line.startswith('__version__'):
                delim = '"' if '"' in line else "'"
                return line.split(delim)[1]
        else:
            raise RuntimeError("Unable to find version string.")


with open('README.md') as f:
    long_description = f.read()

setup(name='medio',
      version=get_version("medio/__init__.py"),
      description='Medical images I/O python package',
      long_description=long_description,
      long_description_content_type='text/markdown',
      url='https://github.com/RSIP-Vision/medio',
      author='RSIP Vision',
      author_email='info@rsipvision.com',
      keywords=['medical-images', 'IO', 'itk', 'nibabel', 'pydicom', 'python'],
      packages=find_packages(exclude=['*.tests']),
      install_requires=[
          'itk >= 5.1.2',
          'nibabel >= 3.2.1',
          'pydicom >= 2.1.2',
          'dicom-numpy >= 0.5.0',
          'numpy >= 1.18.1',
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

          'Operating System :: OS Independent',
      ],
      license='Apache License 2.0',
      zip_safe=True)
