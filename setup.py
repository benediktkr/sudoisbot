from distutils.core import setup

setup(
    name="sudoisbot",
    version="0.0.1-dev",
    packages=[
        'sudoisbot',
    ],
    license="GPL",
    long_description=open('README.md').read(),
    install_requires=[
        'python-telegram-bot',
        'python-daemon',
    ]
)
