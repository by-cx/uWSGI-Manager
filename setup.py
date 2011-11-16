#!/usr/bin/python

import os
from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "uwsgi-manager",
    version = "0.1.1",
    author = "Adam Strauch",
    author_email = "cx@initd.cz",
    description = ("Python tool for controling the uWSGI instances."),
    license = "BSD",
    keywords = "uwsgi",
    url = "https://github.com/creckx/uWSGI-Manager",
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    long_description="This is python tool for controling the uWSGI instances. It can read your XML configuration and stop/reload/restart/start/whatever with your uWSGI processes.",#read('README'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
    install_requires=[
        
        ],
    entry_points="""
    [console_scripts]
    uwsgi-manager = uwsgi_manager.manager:main
    """
)
