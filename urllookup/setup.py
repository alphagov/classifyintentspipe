from setuptools import setup, find_packages

setup(name='govukurllookup',
      version='0.1.0',
      description='Lookup GOV.UK urls with the content API',
      url='http://github.com/ukgovdatascience/classifyintentspipe',
      author='Matthew Upson',
      packages = find_packages(exclude=['tests']),
      author_email='matthew.upson@digital.cabinet-office.gov.uk',
      license='OGL',
      zip_safe=False,
      install_requires=['pandas']
      )
