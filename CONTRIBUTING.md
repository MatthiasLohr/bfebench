# Contributing

## Code Conventions

### Code Styles

This project follows the [PEP8 Style Guide for Python Code](https://www.python.org/dev/peps/pep-0008/)
with only one deviation:
We allow line length to be 120 characters instead of 80.

To test the code against PEP8 rules, you can use `flake8` (install with `pip install flake8`).
All code style rules are configured in `setup.cfg`,
so for a check you can just call `flake8` without any additional parameters.


### Type Hints

This project uses [PEP 484 type hints](https://www.python.org/dev/peps/pep-0484/) to add static type hints to the code.
Typing hints and correct usage can be tested using `mypy` (install with `pip install mypy`).
All configuration for `mypy` is done in `setup.cfg`,
so for a check you can just call `mypy` without any additional parameters.
