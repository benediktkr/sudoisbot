import configparser

from sudoisbot import __version__


def test_version():
    pyproject = configparser.ConfigParser()
    pyproject.read("pyproject.toml")
    assert __version__ == pyproject['tool.poetry']['version'].strip('"')
