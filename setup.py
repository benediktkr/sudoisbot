from distutils.core import setup

setup(
    name="sudoisbot",
    version="0.0.1-dev",
    packages=[
        'sudoisbot',
    ],
    license="GPL",
    description="Telegram bot for sudo.is systems",
    long_description=open('README.md').read(),
    install_requires=[
        'python-telegram-bot',
        'python-daemon',
    ],
    scripts=[
        'bin/listener.py',
        'bin/sendmsg.py',
    ],
)
