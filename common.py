import os
import yaml


def getconfig(filename=".sudoisbot.yml"):
    homedir = os.path.expanduser("~")
    conffile = os.path.join(homedir, filename)
    with open(conffile, 'r') as cf:
        config = yaml.load(cf)
    return config
    
def name_user(update):
    user = update.message.from_user
    for param in ['username', 'first_name', 'id']:
        name = getattr(user, param, False)
        if name:
            return name

def codeblock(text):
    code = "```\n{}```".format(text)
    return code
