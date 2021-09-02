# This file is part of the Blockchain-based Fair Exchange Benchmark Tool
#    https://gitlab.com/MatthiasLohr/bfebench
#
# Copyright 2021 Matthias Lohr <mail@mlohr.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from setuptools import setup, find_packages  # type: ignore


with open('README.md', 'r') as fp:
    long_description = fp.read()


setup(
    name='bfebench',
    description='Blockchain-based Fair Exchange Benchmark Tool',
    long_description=long_description,
    long_description_content_type='text/markdown',
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    author='Matthias Lohr',
    author_email='mail@mlohr.com',
    url='https://gitlab.com/MatthiasLohr/bfebench',
    license='Apache License 2.0',
    install_requires=[
        'hexbytes==0.2.1',
        'Jinja2==3.0.1',
        'pycryptodome==3.10.1',
        'py-solc-x==1.1.0',
        'PyYAML==5.4.1',
        'tabulate==0.8.9',
        'web3==5.21.0'
    ],
    python_requires='>=3.7.*, <4',
    packages=find_packages(exclude=['tests', 'tests.*']),
    package_data={
        '': ['*.sol'],
        'bfebench': ['py.typed']
    },
    entry_points={
        'console_scripts': [
            'bfebench=bfebench.cli.main:main'
        ]
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: Unix',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Solidity',
        'Topic :: Scientific/Engineering',
    ],
    project_urls={
        # 'Documentation': 'https://bfebench.readthedocs.io/',
        'Source': 'https://gitlab.com/MatthiasLohr/bfebench',
        'Tracker': 'https://gitlab.com/MatthiasLohr/bfebench/issues'
    }
)
