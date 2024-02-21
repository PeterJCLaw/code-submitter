# Code Submitter

[![CircleCI](https://circleci.com/gh/PeterJCLaw/code-submitter.svg?style=svg)](https://circleci.com/gh/PeterJCLaw/code-submitter)

Code submitter for Student Robotics Virtual Competition.

## Deployment

Typical deployment is at `/code-submitter/` behind an HTTP proxy which can e.g: add TLS termination.
An example deployment is at <https://github.com/srobo/ansible/tree/main/roles/code-submitter>.

## Downloading submissions

Access to the uploaded submissions is available either:

* through the web interface by logging in as a user which has access to the
  `blueshirt` scope, see for example how the `FileBackend` handles assigning
  this, or
* via the `./code_submitter/extract_archives.py` script if you have access to
  the machine hosting the deployment

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
