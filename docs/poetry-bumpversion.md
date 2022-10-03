# `poetry-bumpversion` and working around PEP 440 errors

install the `poetry-bumpversion` plugin as [per the poetry
docs](https://python-poetry.org/docs/plugins/#the-self-add-command),
since it isnt part of the poetry repo, but the poetry setup on the
system:

```shell
poetry self add poetry-bumpversion
```

poetry 1.2.0 is a lot more careful/specific about version numbers, if
you get an error like

```
Invalid PEP 440 version: '1.1build1'
```

that means that poetry found a package installed on your system that
doesnt follow PEP 440 versioning.

use `python3 -m pip freeze` to find which package it is. on Debian and
Ubuntu it is likely to be a package installed by apt (intalled in
`/usr/lib/python3/dist-packages`), and in this case the package is
`distro-info`.

```shell
$ python3 -m pip freeze | grep "build1"
distro-info===1.1build1
$ apt-cache policy python3-distro-info
python3-distro-info:
  Installed: 1.1build1
```

so the ubuntu package `python3-distro-info` is installed into
`dist-packages` with an uncompliant version string.

## install poetry with `pipx`

following [the docs](https://python-poetry.org/docs/#installing-with-pipx),
first install `pipx`:

```shell
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# on ubuntu, to get `ensurepip`:
sudo apt-get install python3.10-venv
```

and then install `poetry` into a `pipx` managed venv:

```shell
pipx install poetry
```

this will create a virtual environment at `~/.local/pipx/venvs` and
install `poetry` there. it also creates a symlink at `~/.local/bin/poetry`:

```shell
# which poetry
~/.local/bin/poetry
```

and then just add the `poetry-bumpversion` plugin:

```shell
poetry add poetry-bumpversion
```

now it works, the `poetry-bumpversion` plugin updates files according to our settings in `pyproject.toml`:

```shell
$ poetry version patch
Bumping version from 0.4.10 to 0.4.11

$ git status --short
 M pyproject.toml
 M sudoisbot/__init__.py

```

since `pipx` doesnt care about `dist-packages`, the ubuntu-maintened
`dist-packages` was ignored, since `pipx` doesnt look at it (being in
a venv).


## workaround for poetry installed with pip

you can run `poetry` inside its own managed venv, because that [wont
have access to the `site-packages` by
default](https://python-poetry.org/docs/plugins/#the-self-add-command).

check the value of `virtualenvs.options.system-site-packages`

```shell
$ poetry config virtualenvs.options.system-site-packages
false
```

if you need to change it:

```shell
poetry config virtualenvs.options.system-site-packages false
```

now you can use it like this:

```shell
$ poetry run python3 -m poetry self add poetry-bumpversion
$ poetry run python3 -m poetry version patch
Bumping version from 0.4.10 to 0.4.11
```

and it will have updated the files you configured it to update in
`pyproject.toml` (usually `$package/__init__.py`).

unfortuately it doesnt help to add it to your projects dependencies,
your local `site-packages` with `--user` or install into the venv that
poetry manages, since `poetry self` doesnt use that (unless we pull a
fast one poetry and run it from within its own venv).
