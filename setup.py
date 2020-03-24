from setuptools import setup, find_packages

setup(name='medio',
      version='0.0',
      description='Medical images I/O python package',
      url='https://gitlab.com/rsip/medio',
      author='Jonathan Daniel',
      author_email='jonathan@rsipvision.com',
      packages=find_packages(exclude=['*.tests']),  # TODO: exclude does not work apparently
      install_requires=[
            'itk',  # TODO: Maybe only itk-io + itk-filtering (for itk.OrientImageFilter)?
            'nibabel',
            'dicom-numpy',
            'pydicom',
            'numpy'
      ],
      zip_safe=False)
