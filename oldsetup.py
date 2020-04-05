from setuptools import setup

setup(
    name="sudoisbot",
    version="0.0.5-dev",
    url="https://github.com/benediktkr/sudoisbot",
    maintainer="Ben Kristinsson",
    maintainer_email="ben@lokun.is",
    packages=[
        'sudoisbot',
    ],
    license="GPL",
    description="Telegram bot for sudo.is systems",
    long_description=open('README.md').read(),
    install_requires=[
        'python-telegram-bot',
        'python-daemon',
        'PyYAML',
    ],
    scripts=[
        'bin/tglistener.py',
        'bin/sendtelegram.py',
    ],
    entry_points = {
        'console_scripts': [
            'listener=sudoisbot.listener:main',
        ]
    },
)