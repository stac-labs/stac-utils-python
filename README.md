# stac-utils-python
Python utilities library for stac labs.

Copyright 2022 stac labs. See LICENSE.md for licensing.

## Usage

To use this library in your project, place the following line in your `requirements.txt` file:

```
stac_utils_python @ git+https://github.com/stac-labs/stac-utils-python.git@[version]
```

where `version` can be used to match a tag for the version of the code you'd like to use. If not specified, the latest version on main will be used. 

## Development

Run `pip install -r requirements.txt` to install dependencies into your virtual environment necessary for development and local testing.

Run `python -m build .` to build both a `.tar` and `.whl` package in the `dist` folder.

Running the `pytest` command will run all tests in `src/tests`.

## Bumping versions
By default, CircleCI will bump the package version and the associated git tag at the patch level, on merge to `main`. For a major or minor release, you will want to do a manual release using `python -m bumpversion major` or `python -m bumpversion minor`, and then `git push origin --tags`.