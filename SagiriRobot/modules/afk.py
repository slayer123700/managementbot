import time
import random

from typing import Optional
from datetime import datetime
from telegram import Message, User
from telegram import MessageEntity, ParseMode
from telegram.error import BadRequest
from telegram.ext import Filters, MessageHandler, run_async

from SagiriRobot import dispatcher
from SagiriRobot.modules.disable import DisableAbleCommandHandler, DisableAbleMessageHandler
from SagiriRobot.modules.redis.afk_redis import start_afk, end_afk, is_user_afk, afk_reason
from SagiriRobot import REDIS
from SagiriRobot.modules.users import get_user_id

from SagiriRobot.modules.helper_funcs.alternate import send_message
from SagiriRobot.modules.helper_funcs.readable_time import get_readable_time

AFK_GROUP = 7
AFK_REPLY_GROUP = 8

AFKVID = "https://te.legra.ph/file/457ef1771a4c4f2127ec3.mp4"


def afk(update, context):
    args = update.effective_message.text.split(None, 1)
    user = update.effective_user
    if not user:  # ignore channels
        return

    if user.id == 777000:
        return
    start_afk_time = time.time()
    reason = args[1] if len(args) >= 2 else "none"
    start_afk(update.effective_user.id, reason)
    REDIS.set(f'afk_time_{update.effective_user.id}', start_afk_time)
    fname = update.effective_user.first_name
    try:
        update.effective_message.reply_video(
            AFKVID,caption="Bʏɪɪ ʙʏɪɪ.  𝚂ᴀʏᴏɴᴀʀᴀᴀ...👋  {}!".format(fname))
    except BadRequest:
        pass

def no_longer_afk(update, context):
    user = update.effective_user
    message = update.effective_message
    if not user:  # ignore channels
        return

    if not is_user_afk(user.id):  #Check if user is afk or not
        return
    end_afk_time = get_readable_time((time.time() - float(REDIS.get(f'afk_time_{user.id}'))))
    REDIS.delete(f'afk_time_{user.id}')
    res = end_afk(user.id)
    if res:
        if message.new_chat_members:  # dont say msg
            return
        firstname = update.effective_user.first_name
        try:
            options = [
                "{} I know what you were doing.😏✊.\nAnyway, welcome back! Time Taken: {}",
                "Hey, {} I glad to know that! you're watching some Chad videos since {}",
                "Welcome back, {} Btw why are spending your time with your step mother? since {}",
                "Guys, {} got a girlfried, that's why he was busy since {}",
                "Dear {}, Are you a BTS Lover. I know you were watching it since {}",
                "Guys {}, is watching some videos of mia khalifa that was why he was busy since {}",
                "The Dead {} Came Back From His Grave! Time Taken: {}",
                "Hey {} Darling, Welcome Back! We Were Apart For {}",
                "{} Came Back After Masturbating! Time Taken: {}",
                "OwO, Welcome Back {}! You Were Missing Since {} ",
            ]
            chosen_option = random.choice(options)
            update.effective_message.reply_text(
                chosen_option.format(firstname, end_afk_time),
            )
        except BaseException:
            pass
            



def reply_afk(update, context):
    message = update.effective_message
    userc = update.effective_user
    userc_id = userc.id
    if message.entities and message.parse_entities(
        [MessageEntity.TEXT_MENTION, MessageEntity.MENTION]):
        entities = message.parse_entities(
            [MessageEntity.TEXT_MENTION, MessageEntity.MENTION])

        chk_users = []
        for ent in entities:
            if ent.type == MessageEntity.TEXT_MENTION:
                user_id = ent.user.id
                fst_name = ent.user.first_name

                if user_id in chk_users:
                    return
                chk_users.append(user_id)

            elif ent.type == MessageEntity.MENTION:
                user_id = get_user_id(message.text[ent.offset:ent.offset +
                                                   ent.length])
                if not user_id:
                    # Should never happen, since for a user to become AFK they must have spoken. Maybe changed username?
                    return

                if user_id in chk_users:
                    return
                chk_users.append(user_id)

                try:
                    chat = context.bot.get_chat(user_id)
                except BadRequest:
                    print("Error: Could not fetch userid {} for AFK module".
                          format(user_id))
                    return
                fst_name = chat.first_name

            else:
                return

            check_afk(update, context, user_id, fst_name, userc_id)

    elif message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        fst_name = message.reply_to_message.from_user.first_name
        check_afk(update, context, user_id, fst_name, userc_id)


def check_afk(update, context, user_id, fst_name, userc_id):
    if is_user_afk(user_id):
        reason = afk_reason(user_id)
        since_afk = get_readable_time((time.time() - float(REDIS.get(f'afk_time_{user_id}'))))
        if int(userc_id) == int(user_id):
            return
        if reason == "none":
            res = "{} Is With Your GF!\nLast Seen Here: {} Ago.".format(fst_name, since_afk)
        else:
            res = "{} Is Dead!\nReason: {}\nLast Liveliness: {} Ago.".format(fst_name, reason, since_afk)

        update.effective_message.reply_text(res)


def __user_info__(user_id):
    is_afk = is_user_afk(user_id)
    text = ""
    if is_afk:
        since_afk = get_readable_time((time.time() - float(REDIS.get(f'afk_time_{user_id}'))))
        text = "This user is currently afk (away from keyboard)."
        text += f"\nLast Seen: {since_afk} Ago."
       
    else:
        text = "This user currently isn't afk (not away from keyboard)."
    return text

def __stats__():
    return f"• {len(REDIS.keys())} Total Keys in Redis Database."

def __gdpr__(user_id):
    end_afk(user_id)

__mod_name__ = "Aꜰᴋ"
__help__ = """
  When marked as AFK, any mentions will be replied to with a message stating that you're not available!
 • `/afk <reason>`*:* Mark yourself as AFK.
 - `brb <reason>`*:* Same as the afk command, but not a command.
"""


AFK_HANDLER = DisableAbleCommandHandler("afk", afk, run_async=True)
AFK_REGEX_HANDLER = MessageHandler(Filters.regex("(?i)brb"), afk)
NO_AFK_HANDLER = MessageHandler(Filters.all & Filters.chat_type.groups, no_longer_afk, run_async=True)
AFK_REPLY_HANDLER = MessageHandler(Filters.all & Filters.chat_type.groups, reply_afk, run_async=True)

dispatcher.add_handler(AFK_HANDLER, AFK_GROUP)
dispatcher.add_handler(AFK_REGEX_HANDLER, AFK_GROUP)
dispatcher.add_handler(NO_AFK_HANDLER, AFK_GROUP)
dispatcher.add_handler(AFK_REPLY_HANDLER, AFK_REPLY_GROUP)
