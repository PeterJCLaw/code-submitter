import os.path

from setuptools import setup, find_packages


my_dir = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(my_dir, 'README.md')) as f:
    long_description = f.read()


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

    classifiers=(
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Web Environment',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ),
)
