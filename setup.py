#!/usr/bin/env python

"""The setup script."""

from setuptools import find_packages, setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('CHANGES.rst') as history_file:
    history = history_file.read()

setup(
    author='riscLOG Solution GmbH',
    author_email='info@risclog.de',
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: German',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    description='A logger based on structlog',
    install_requires=[
        # Add your dependencies here
        'structlog',
    ],
    extras_require={
        'docs': [
            'Sphinx',
        ],
        'test': [
            'pytest-cache',
            'pytest-cov',
            'pytest-flake8',
            'pytest-rerunfailures',
            'pytest-sugar',
            'pytest',
            'coverage',
            # https://github.com/PyCQA/flake8/issues/1419#issuecomment-947243876
            'flake8<4',
            'mock',
            'requests',
            'httpx',
            'pytest-asyncio',
        ],
    },
    license='MIT license',
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='risclog.logging',
    name='risclog.logging',
    packages=find_packages('src'),
    namespace_packages=['risclog'],
    package_dir={'': 'src'},
    url='https://github.com/risclog-solution/risclog.logging',
    version='1.2.1',
    zip_safe=False,
)
