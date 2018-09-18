import os
import yaml


def getconfig():
    homedir = os.path.expanduser("~")
    locations = [
        os.path.join(homedir, ".sudoisbot.yml"),
        os.path.join('/etc', "sudoisbot.yml"),
    ]
    for conffile in locations:
        try:
            with open(conffile, 'r') as cf:
                config = yaml.load(cf)
            return config
        except IOError as e:
            if e.errno == 2: continue
            else: raise
    raise ValueError("No config file found")
    
def name_user(update):
    user = update.message.from_user
    for param in ['username', 'first_name', 'id']:
        name = getattr(user, param, False)
        if name:
            return name

def codeblock(text):
    code = "```\n{}```".format(text)
    return code
