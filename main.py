import requests
import json
import random
import string
from telegram import Update, ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, MessageHandler, Filters

BOT_TOKEN = "7819656172:AAFo9XjkRk6LXfVHArkeMn_4uLIzyqzHp10"  # Replace with your bot token
STRIPE_SK = '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'

application = ApplicationBuilder().token(BOT_TOKEN).build()

def get_str(string, start, end):
    try:
        return (string.split(start))[1].split(end)[0]
    except IndexError:
        return None


def random_string(length):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    chat_id = update.message.chat.id
    response = f"<b>Telegram ID:</b> <code>{user_id}</code>\n" \
               f"<b>Group ID: </b><code>{chat_id}</code>\n" \
               f"<b>To Know Commands: /cmds</b>"
    context.bot.send_message(chat_id=chat_id, text=response, parse_mode=ParseMode.HTML)


def cmds(update: Update, context: CallbackContext):
    chat_id = update.message.chat.id
    response = ("<b><i>[Checker Gates]\n\nSTRIPE CUSTOM CHARGE -\n" \
                "/chk {Amount In $} - xxxxxxxxxxxxxxxx|xx|xx|xxx\n" \
                "/inr {Amount In \u20b9} - xxxxxxxxxxxxxxxx|xx|xx|xxx\n" \
                "BIN LOOKUP - /bin -  xxxxxx\n" \
                "SK CHECK - /sk -  sk_live_xxxxxxxxxx\n" \
                "[Tools]\n\nTELEGRAM ID/GROUP ID - /id</i></b>")
    context.bot.send_message(chat_id=chat_id, text=response, parse_mode=ParseMode.HTML)


def chk(update: Update, context: CallbackContext):
    chat_id = update.message.chat.id
    user_name = update.message.from_user.username
    message = update.message.text[5:]
    details = message.split('|')

    if len(details) < 4:
        context.bot.send_message(chat_id=chat_id, text="❌ Invalid Card Details\nFormat - /chk xxxxxxxxxxxxxxxx|xx|xx|xxx", parse_mode=ParseMode.HTML)
        return

    # Parsing card details
    cc, mes, ano, cvv = details[:4]
    amount = 1 * 100  # Default amount, can be changed as needed

    # Using BIN Lookup API
    response = requests.get(f'https://lookup.binlist.net/{cc[:6]}')
    bin_info = response.json()
    bank = bin_info.get('bank', {}).get('name', 'N/A')
    brand = bin_info.get('brand', 'N/A')
    country = bin_info.get('country', {}).get('name', 'N/A')
    emoji = bin_info.get('country', {}).get('emoji', '')
    scheme = bin_info.get('scheme', 'N/A')
    card_type = bin_info.get('type', 'N/A')

    # Creating Payment Method
    payload = {
        "type": "card",
        "card[number]": cc,
        "card[exp_month]": mes,
        "card[exp_year]": ano,
        "card[cvc]": cvv
    }
    headers = {'Authorization': f'Bearer {STRIPE_SK}'}
    response = requests.post('https://api.stripe.com/v1/payment_methods', data=payload, headers=headers)
    result = response.json()
    payment_method_id = result.get("id")

    if payment_method_id:
        # Creating Payment Intent
        payload = {
            "amount": amount,
            "currency": "usd",
            "payment_method": payment_method_id,
            "confirmation_method": "manual",
            "confirm": "true",
        }
        response = requests.post('https://api.stripe.com/v1/payment_intents', data=payload, headers=headers)
        result = response.json()

        if "status" in result and result["status"] == "succeeded":
            response_message = f"<b>Card:</b> <code>{cc}|{mes}|{ano}|{cvv}</code>\n" \
                              f"<b>Status:</b> ✅ CVV Matched\n" \
                              f"<b>Response:</b> Successfully Charged ${amount/100}\n" \
                              f"<b>Checked By:</b> @{user_name}"
        else:
            response_message = f"<b>Card:</b> <code>{cc}|{mes}|{ano}|{cvv}</code>\n" \
                              f"<b>Status:</b> ❌ Declined\n" \
                              f"<b>Response:</b> {result.get('error', {}).get('message', 'Unknown error')}\n" \
                              f"<b>Checked By:</b> @{user_name}"
    else:
        response_message = f"<b>Card:</b> <code>{cc}|{mes}|{ano}|{cvv}</code>\n" \
                          f"<b>Status:</b> ❌ Declined\n" \
                          f"<b>Response:</b> {result.get('error', {}).get('message', 'Invalid card details')}\n" \
                          f"<b>Checked By:</b> @{user_name}"

    context.bot.send_message(chat_id=chat_id, text=response_message, parse_mode=ParseMode.HTML)


# Adding Handlers
application.add_handler(CommandHandler('start', start))
application.add_handler(CommandHandler('cmds', cmds))
application.add_handler(CommandHandler('chk', chk))

# Running the bot
application.run_polling()
