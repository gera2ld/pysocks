#!/usr/bin/env python
# coding=utf-8
from setuptools import setup, find_packages

setup(
    name='pysocks',
    version='1.0',
    packages=find_packages(exclude=['tests']),
    author='Gerald',
    author_email='i@gerald.top',
    description='SOCKS client and server.',
    url='https://github.com/gera2ld/pysocks',
)
