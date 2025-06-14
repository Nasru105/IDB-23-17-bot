from telegram import Update
from telegram.ext import ContextTypes
from services.storage import load_data, save_data
from utils.utils import reformat, safe_delete, get_queue_keyboard, get_time

# Загружаем сохранённые данные из файла и приводим ключи к нужному формату (int вместо str)
queues, last_queue_message = reformat(*load_data())

# Добавление пользователя в очередь
def add_to_queue(chat, user):
    queues.setdefault(chat.id, [])  # Если для чата ещё нет очереди — создаём пустую
    if user not in queues[chat.id]:  # Добавляем пользователя, если его ещё нет
        queues[chat.id].append(user)
        save_data(queues, last_queue_message)  # Сохраняем изменения
        print(f"{chat.title if chat.title else chat.username}: {get_time()} join {user} ({len(queues[chat.id])})", flush=True)


# Удаление пользователя из очереди
def remove_from_queue(chat, user):
    # Удаляем пользователя, если он есть, и сохраняем
    position = queues[chat.id].index(user)
    queues.get(chat.id, []).remove(user) if user in queues.get(chat.id, []) else None
    save_data(queues, last_queue_message)
    print(f"{chat.title if chat.title else chat.username}: {get_time()} leave {user} ({position + 1})", flush=True)


# Получить очередь по chat_id
def get_queue(chat_id):
    return queues.get(chat_id, [])

# Получить ID последнего отправленного ботом сообщения об очереди
def get_last_message_id(chat_id):
    return last_queue_message.get(chat_id)

# Установить ID последнего сообщения и сохранить изменения
def set_last_message_id(chat_id, msg_id):
    last_queue_message[chat_id] = msg_id
    save_data(queues, last_queue_message)

# Сформировать текст очереди для отображения
def get_queue_text(chat_id):
    q = get_queue(chat_id)
    text = "\n".join(f"{i + 1}. {u}" for i, u in enumerate(q)) if q else "Очередь пуста."
    return text

async def sent_queue_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message_thread_id = update.message.message_thread_id

    last_id = get_last_message_id(chat.id)
    if last_id:
        await safe_delete(context, chat, last_id)

    sent = await context.bot.send_message(
        chat_id=chat.id,
        text=get_queue_text(chat.id),
        reply_markup=get_queue_keyboard(),
        message_thread_id=message_thread_id
    )

    set_last_message_id(chat.id, sent.message_id)