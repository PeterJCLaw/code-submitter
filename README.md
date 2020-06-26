# Code Submitter

[![CircleCI](https://circleci.com/gh/PeterJCLaw/code-submitter.svg?style=svg)](https://circleci.com/gh/PeterJCLaw/code-submitter)

Code submitter for Student Robotics Virtual Competition.

## Development setup

Install the project itself:

``` shell
$ pip install -e .
```

Install the linters and other tools:

``` shell
$ pip install -r script/dev-requirements.txt
```

You'll also need an ASGI server, such as [uvicorn](http://www.uvicorn.org/):

``` shell
$ pip install uvicorn
```

Run the project:

``` shell
$ ./script/uvicorn
```
