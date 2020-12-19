# Code Submitter

[![CircleCI](https://circleci.com/gh/PeterJCLaw/code-submitter.svg?style=svg)](https://circleci.com/gh/PeterJCLaw/code-submitter)

Code submitter for Student Robotics Virtual Competition.

## Development setup

Install all the things:

``` shell
$ pip install -e . -r script/dev-requirements.txt uvicorn
```

Run the checks:

``` shell
$ ./script/check
```

Create/update the database schema:

``` shell
alembic upgrade head
```

Run the server:

``` shell
$ ./script/uvicorn
```

## Coding style

This repo generally follows [Thread's Python coding style](https://www.notion.so/Python-Style-Guide-093dc870df7e491caa5e4a2e8c0be52f).
