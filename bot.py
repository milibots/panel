import telebot
from telebot import types
import time
import os

# --- Configuration ---
# It's highly recommended to use environment variables for sensitive data like tokens
BOT_TOKEN = os.environ.get('YOUR_BOT_TOKEN', '7510687910:AAHzTkago5oH0oVuLMbHjSx-7Pq9NG8jv3M')
# Ensure CHANNEL_ID is an integer (supergroups/channels start with -100)
try:
    # Use integer for comparisons and API calls
    TARGET_CHAT_ID = int("-1002692959413")
except ValueError:
    print("ERROR: CHANNEL_ID must be a valid integer.")
    exit()
# Chat ID where reports/errors will be sent (your user ID or another chat)
try:
    REPORT_CHAT_ID = int("5361491365")
except ValueError:
    print("ERROR: REPORT_CHAT_ID must be a valid integer.")
    exit()

if BOT_TOKEN == 'YOUR_BOT_TOKEN':
    print("ERROR: Please set your BOT_TOKEN environment variable or replace the placeholder.")
    exit()
if TARGET_CHAT_ID == -1:
    print("ERROR: Please set your CHANNEL_ID.")
    exit()
if REPORT_CHAT_ID == -1:
    print("ERROR: Please set your REPORT_CHAT_ID.")
    exit()

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

print(f"Bot initialized. Monitoring chat ID: {TARGET_CHAT_ID}")
print(f"Reports will be sent to chat ID: {REPORT_CHAT_ID}")

# --- Bot Commands ---
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Sends a welcome message."""
    # Avoid processing commands in the target chat if not intended
    if message.chat.id == TARGET_CHAT_ID:
        return
    bot.reply_to(message, f"Hello! I am running and monitoring chat {TARGET_CHAT_ID} to remove new members.")

# --- Core Logic: Handle Member Status Changes ---
@bot.chat_member_handler()
def handle_chat_member_updates(message: types.ChatMemberUpdated):
    """
    Handles updates about chat member status changes (join, leave, etc.).
    This is generally more reliable than 'new_chat_members' message content type.
    """
    try:
        chat_id = message.chat.id
        # Extract new member information
        new_member_status = message.new_chat_member.status
        user = message.new_chat_member.user

        print(f"Chat Member Update in Chat ID: {chat_id}")
        print(f"User: {user.id} ({user.first_name}), New Status: {new_member_status}")

        # --- Check if it's the target chat and a user actually joined ---
        if chat_id == TARGET_CHAT_ID and new_member_status == 'member':
            print(f"--> New member detected in target chat {TARGET_CHAT_ID}: User {user.id} ({user.first_name})")
            process_new_member(message.chat, user)

    except Exception as e:
        print(f"Error in chat_member_handler: {e}")
        try:
            bot.send_message(REPORT_CHAT_ID, f"⚠️ Error in chat_member_handler: {str(e)}")
        except Exception as report_e:
            print(f"Failed to send error report: {report_e}")

def process_new_member(chat: types.Chat, user: types.User):
    """
    Bans and then immediately unbans a new member to effectively remove them.
    """
    user_info = f"{user.first_name} {user.last_name or ''}".strip()
    user_id = user.id
    username = f"@{user.username}" if user.username else "N/A"
    chat_title = chat.title if chat.title else f"Chat {chat.id}"

    print(f"Processing User ID: {user_id} ({user_info}) in chat '{chat_title}' ({chat.id})")

    try:
        # 1. Ban the user (removes them from the chat)
        print(f"Attempting to ban User ID: {user_id}")
        # `revoke_messages=True` can delete messages they might have sent immediately upon joining
        bot.ban_chat_member(chat.id, user_id, revoke_messages=True)
        print(f"Successfully banned User ID: {user_id}")
        # Short delay might sometimes help ensure the ban is processed by Telegram servers
        time.sleep(1)

        # 2. Unban the user (allows them to be invited back, but prevents rejoining via link for a bit)
        print(f"Attempting to unban User ID: {user_id}")
        # `only_if_banned=True` is good practice, ensures we only unban if the ban succeeded
        bot.unban_chat_member(chat.id, user_id, only_if_banned=True)
        print(f"Successfully unbanned User ID: {user_id}")

        # 3. Send Report
        report_msg = (
            f"✅ New member processed in '{chat_title}'\n"
            f"👤 User: {user_info}\n"
            f"🆔 ID: `{user_id}`\n" # Use backticks for easy copying
            f"✉️ Username: {username}\n"
            f"🔨 Action: Banned & Unbanned (Removed)"
        )
        bot.send_message(REPORT_CHAT_ID, report_msg, parse_mode="Markdown")
        print(f"Report sent for User ID: {user_id}")

    except Exception as e:
        error_msg = (
            f"⚠️ Error processing new member in '{chat_title}'\n"
            f"👤 User: {user_info}\n"
            f"🆔 ID: `{user_id}`\n"
            f"✉️ Username: {username}\n"
            f"❌ Error: {str(e)}"
        )
        print(f"Error processing User ID {user_id}: {e}")
        try:
            bot.send_message(REPORT_CHAT_ID, error_msg, parse_mode="Markdown")
        except Exception as report_e:
            print(f"Failed to send error report: {report_e}")


# --- Optional: Handler for Bot's Own Status ---
@bot.my_chat_member_handler()
def handle_my_status(message: types.ChatMemberUpdated):
    """Logs when the bot's own status changes in a chat."""
    chat_id = message.chat.id
    chat_title = message.chat.title if message.chat.title else f"Chat {chat_id}"
    old_status = message.old_chat_member.status
    new_status = message.new_chat_member.status
    print(f"Bot status change in '{chat_title}' ({chat_id}): {old_status} -> {new_status}")

    # Check if the bot was added to the target chat and has ban permissions
    if chat_id == TARGET_CHAT_ID and new_status == 'administrator':
        try:
            my_info = bot.get_chat_member(chat_id, bot.get_me().id)
            if my_info.can_restrict_members:
                print(f"Bot is admin in target chat and HAS ban permissions.")
                bot.send_message(REPORT_CHAT_ID, f"ℹ️ Bot is now admin in '{chat_title}' with ban permissions.")
            else:
                print(f"WARNING: Bot is admin in target chat but DOES NOT have ban permissions!")
                bot.send_message(REPORT_CHAT_ID, f"⚠️ Bot is admin in '{chat_title}' but **LACKS BAN PERMISSIONS**! It cannot remove new members.")
        except Exception as e:
             print(f"Could not check bot permissions in {chat_id}: {e}")


# --- Start the Bot ---
if __name__ == '__main__':
    print("Starting bot polling...")
    # Ensure the bot listens for the necessary update types
    # 'message' for commands, 'chat_member' for joins/leaves/status changes
    allowed_updates = ['message', 'chat_member', 'my_chat_member']
    print(f"Allowed updates: {allowed_updates}")
    bot.infinity_polling(allowed_updates=allowed_updates, skip_pending=True)
    # skip_pending=True avoids processing updates that arrived while the bot was offline