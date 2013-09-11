import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
read_file = lambda filename: open(os.path.join(here, filename)).read()
read_requirements = lambda filename: read_file(filename).splitlines()

TEST_REQUIREMENTS = read_requirements('requirements-test.txt')

setup(
    name='Flask-CuddlyRest',
    version='0.1.9',
    url='http://github.com/wuurrd/flask-cuddlyrest',
    license='MIT',
    author='David Buchmann',
    author_email='david.buchmann@gmail.com',
    maintainer='David Buchmann',
    maintainer_email='david.buchmann@gmail.com',
    description='Flask restful API framework for MongoDB/MongoEngine',
    long_description=read_file('README.md'),
    packages=find_packages(),
    zip_safe=False,
    install_requires=read_requirements('requirements.txt'),
    tests_require=TEST_REQUIREMENTS,
    extras_require={
        'test': TEST_REQUIREMENTS,
    },
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
