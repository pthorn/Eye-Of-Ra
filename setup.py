import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

requires = [
    'pyramid >= 1.5.1',
    'transaction >= 1.4.3',
    'pyramid_tm >= 0.7',
    'pyramid_debugtoolbar >= 2.1',
    'pyramid_exclog',
    'pyramid_mako >= 1.0.2',
    'mako >= 1.0.0',
    'waitress >= 0.8.9',

    'SQLAlchemy >= 0.9.6',
    'zope.sqlalchemy >= 0.7.5',
    'psycopg2 >= 2.5.3',

    'Beaker >= 1.6.4',
    'pyramid_beaker >= 0.8',

    'passlib >= 1.6.2',

    'colander',
    'peppercorn',

    'pytz',
    'tzlocal',
    'python-dateutil >= 2.2',

    'markdown',
    #'pyembed-markdown',
    'bleach',

    'pillow >= 2.6.1',

    #'lxml == 2.3.5',

    'requests >= 2.3.0',
    'rauth >= 0.7.0'
]

setup(
    name='eye-of-ra',
    version='1.0',
    description='A web application toolkit for the Pyramid framework',
    long_description='',
    classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    author='p.thorn.ru@gmail.com',
    author_email='p.thorn.ru@gmail.com',
    url='',
    keywords='web wsgi bfg pylons pyramid',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    test_suite='cms',
    install_requires=requires,
    entry_points="""\
#[console_scripts]
#foo = eor.scripts.foo:main
""",
)
