from setuptools import setup

setup(name='kanripo',
      version='0.1',
      description='Access to the kanripo API.',
      url='http://github.com/mandoku/kanripo',
      author='Christian Wittern',
      author_email='cwittern@gmail.com',
      license='CC by SA',
      packages=['kanripo'],
      install_requires=[
          'requests',
          'PyGithub'
      ],
      zip_safe=False)
