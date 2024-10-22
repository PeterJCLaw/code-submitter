from __future__ import annotations

import os.path

from setuptools import setup, find_packages

my_dir = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(my_dir, 'README.md')) as f:
    long_description = f.read()

with open(os.path.join(my_dir, 'requirements.in')) as f:
    install_requires = [
        x.partition('#')[0].strip()
        for x in f.readlines()
    ]
    install_requires = [x for x in install_requires if x]


setup(
    name='code-submitter',
    version='0.0.1',
    url='https://github.com/PeterJCLaw/code-submitter',
    project_urls={
        'Issue tracker': 'https://github.com/PeterJCLaw/code-submitter/issues',
    },
    description="Code submitter for Student Robotics Virtual Competition.",
    long_description=long_description,
    long_description_content_type='text/markdown',

    packages=find_packages(exclude=['tests']),

    author="Peter Law",
    author_email="PeterJCLaw@gmail.com",

    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Web Environment',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
    ],
    python_requires='>=3.9',

    install_requires=install_requires,
)
