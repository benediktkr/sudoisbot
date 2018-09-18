import config

def check_allowed(bot, update):
    if update.message.from_user.id not in config.authorized_users:
        logger.error("Unauthorized user: {}".format(update.message.from_user))
        update.message.reply_text(config.unauthed_text)
        raise DispatcherHandlerStop

def name_user(update):
    user = update.message.from_user
    for param in ['username', 'first_name', 'id']:
        name = getattr(user, param, False)
        if name:
            return name

def codeblock(text):
    code = "```\n{}```".format(text)
    return code
