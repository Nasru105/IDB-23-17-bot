import random

from telegram import Update
from telegram.ext import ContextTypes

from config import STUDENTS_USERNAMES
from services.queue_service import queues, get_last_message_id, set_last_message_id, get_queue, add_to_queue, \
    sent_queue_message
from utils.utils import safe_delete, get_time


async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Получаем список админов чата
    admins = await context.bot.get_chat_administrators(chat_id)
    # Проверяем, является ли пользователь админом
    return any(admin.user.id == user_id for admin in admins)


async def clear_queue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message_id = update.message.message_id
    await safe_delete(context, chat, message_id)

    if not await is_admin(update, context):
        return

    queues[chat.id] = []
    print(f"{chat.title if chat.title else chat.username}: {get_time()} clear queue", flush=True)

    last_id = get_last_message_id(chat.id)
    await safe_delete(context, chat, last_id)

    set_last_message_id(chat.id, None)


async def insert_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message_id = update.message.message_id

    await safe_delete(context, chat, message_id)

    if not await is_admin(update, context):
        return

    args = context.args
    if not args:
        return

    q = get_queue(chat.id)

    # Разбираем имя и позицию
    try:
        position = int(args[-1]) - 1
        name = " ".join(args[:-1])
    except ValueError:
        position = len(q)
        name = " ".join(args)

    # Корректируем позицию
    position = max(0, min(position, len(q)))

    if name and name not in q:
        q.insert(position, name)
        print(f"{chat.title if chat.title else chat.username}: {get_time()} insert {name} ({position + 1})", flush=True)

    await sent_queue_message(update, context)


async def remove_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message_id = update.message.message_id

    await safe_delete(context, chat, message_id)

    if not await is_admin(update, context):
        return

    args = context.args
    if not args:
        return

    q = get_queue(chat.id)
    name = None
    position = None

    # Пытаемся распарсить позицию
    try:
        if len(args) == 1:
            position = int(args[0]) - 1
            if position < 0 or len(q) <= position:
                raise ValueError
        else:
            name = " ".join(args)
    except ValueError:
        name = " ".join(args)

    # Удаляем по позиции, если она допустима
    if position is not None and 0 <= position < len(q):
        name = q.pop(position)
        print(f"{chat.title if chat.title else chat.username}: {get_time()} remove {name} ({position + 1})", flush=True)
        await sent_queue_message(update, context)
    elif name in q:  # Или по имени
        position = q.index(name)
        q.remove(name)
        print(f"{chat.title if chat.title else chat.username}: {get_time()} remove {name} ({position + 1})", flush=True)
        await sent_queue_message(update, context)


async def replace_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message_id = update.message.message_id

    await safe_delete(context, chat, message_id)

    if not await is_admin(update, context):
        return

    if not context.args or len(context.args) != 2:
        return

    try:
        pos1, pos2 = sorted(map(int, context.args))
    except ValueError:
        return

    pos1 -= 1
    pos2 -= 1

    q = get_queue(chat.id)
    queue_length = len(q)

    if (pos1 == pos2 or
            pos1 < 0 or pos2 < 0 or
            pos1 >= queue_length or pos2 >= queue_length):
        return

    # Perform the swap
    name1 = q[pos1]
    name2 = q[pos2]
    q[pos1], q[pos2] = q[pos2], q[pos1]
    print(
        f"{chat.title if chat.title else chat.username}: {get_time()} replace {name1} ({pos1 + 1}) with {name2} ({pos2 + 1})",
        flush=True)

    await sent_queue_message(update, context)


async def generate_queue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return

    chat = update.effective_chat
    message_id = update.message.message_id
    await safe_delete(context, chat, message_id)

    # Обработка аргумента подгруппы
    args = context.args
    subgroup = args[0].upper() if args and args[0].upper() in ("A", "B") else None

    # Перемешиваем список студентов
    all_students = list(STUDENTS_USERNAMES.values())
    random.shuffle(all_students)

    # Очищаем текущую очередь
    queues[chat.id] = []

    # Добавляем пользователей в очередь по фильтру подгруппы (если задана)
    for username, group in all_students:
        if not subgroup or group == subgroup:
            add_to_queue(chat, username)

    await sent_queue_message(update, context)


async def get_list_of_students(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return

    chat = update.effective_chat
    message_id = update.message.message_id
    await safe_delete(context, chat, message_id)

    # Обработка аргумента подгруппы
    args = context.args
    subgroup = args[0].upper() if args and args[0].upper() in ("A", "B") else None

    # Перемешиваем список студентов
    all_students = list(STUDENTS_USERNAMES.values())

    # Очищаем текущую очередь
    queues[chat.id] = []

    # Добавляем пользователей в очередь по фильтру подгруппы (если задана)
    for username, group in all_students:
        if not subgroup or group == subgroup:
            add_to_queue(chat, username)

    await sent_queue_message(update, context)
