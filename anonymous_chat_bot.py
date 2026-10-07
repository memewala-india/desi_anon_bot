import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    PreCheckoutQueryHandler
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

TOKEN = '8883576881:AAHuJhkB-FYgJ9L7c6ETz2Oq0MKHuSaaHAM'

user_data = {}
waiting_users = {'male': [], 'female': []}
active_chats = {}


def get_user(user_id):
    if user_id not in user_data:
        user_data[user_id] = {
            'gender': None,
            'chats_today': 0,
            'total_chats': 0,
            'premium': False,
            'referrals': 0,
            'bonus_chats': 0,
            'referred_by': None,
        }
    return user_data[user_id]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    u = get_user(user_id)

    # 🔥 Обработка реферальной ссылки
    if context.args and context.args[0].startswith('ref_'):
        try:
            referrer_id = int(context.args[0].replace('ref_', ''))
            if referrer_id != user_id and not u.get('referred_by'):
                u['referred_by'] = referrer_id
                await process_referral(update, context, referrer_id)
        except (ValueError, IndexError):
            pass

    # Если уже в чате
    if user_id in active_chats:
        await update.message.reply_text(
            '🎭 Aap already ek chat mein ho.\n\n'
            '/skip — naya partner\n'
            '/stop — chat khatam'
        )
        return

    # Если уже в очереди
    if u['gender'] and user_id in waiting_users.get(u['gender'], []):
        await update.message.reply_text('⏳ Aap queue mein ho. Partner dhoond rahe hain...')
        return

    # Показываем выбор пола
    keyboard = [
        [InlineKeyboardButton("👦 Male", callback_data='male')],
        [InlineKeyboardButton("👧 Female", callback_data='female')],
    ]

    await update.message.reply_text(
        '🎭 *Desi Anon Chat*\n\n'
        'Kisi bhi anjaan insaan se baat karo — bina naam, bina pehchaan!\n\n'
        '📊 Status: 🆓 Free\n\n'
        '👉 Apna gender choose karo:',
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


async def process_referral(update: Update, context: ContextTypes.DEFAULT_TYPE, referrer_id: int) -> None:
    """Обрабатывает приглашение: даёт бонус пригласившему."""
    referrer = get_user(referrer_id)
    referrer['referrals'] = referrer.get('referrals', 0) + 1
    referrer['bonus_chats'] = referrer.get('bonus_chats', 0) + 5

    friends = referrer['referrals']

    # Premium за 3 друга
    if friends == 3 and not referrer.get('premium_7d'):
        referrer['premium'] = True
        referrer['premium_7d'] = True
        try:
            await context.bot.send_message(
                chat_id=referrer_id,
                text='🎉 *Mubarak ho!* 3 dost bula liye.\n\n'
                     '⭐ Aapko FREE Premium mil gaya — 7 din ke liye!',
                parse_mode='Markdown'
            )
        except Exception:
            pass

    # Premium за 10 друзей
    if friends == 10:
        referrer['premium'] = True
        try:
            await context.bot.send_message(
                chat_id=referrer_id,
                text='🏆 *Shandaar!* 10 dost bula liye.\n\n'
                     '⭐ Aapko LIFETIME Premium mil gaya!',
                parse_mode='Markdown'
            )
        except Exception:
            pass

    # Уведомление о новом друге
    try:
        await context.bot.send_message(
            chat_id=referrer_id,
            text=f'🎁 *+1 dost aaya!*\n\n'
                 f'Total: {friends} dost\n'
                 f'Bonus chats: +5',
            parse_mode='Markdown'
        )
    except Exception:
        pass


async def set_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    gender = query.data
    u = get_user(user_id)

    if user_id in active_chats:
        await query.edit_message_text('Aap already ek chat mein ho. /skip ya /stop bhejo.')
        return

    # Снимаем со старой очереди
    if u['gender'] and user_id in waiting_users[u['gender']]:
        waiting_users[u['gender']].remove(user_id)

    u['gender'] = gender

    gender_text = '👦 Male' if gender == 'male' else '👧 Female'
    await query.edit_message_text(
        f'{gender_text} — set ho gaya!\n\n'
        '⏳ Partner dhoond rahe hain...'
    )

    waiting_users[gender].append(user_id)
    await find_chat_partner(user_id, context)


async def stop_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    if user_id in active_chats:
        partner_id = active_chats.pop(user_id, None)
        if partner_id:
            active_chats.pop(partner_id, None)
            await context.bot.send_message(
                chat_id=partner_id,
                text='❌ Partner ne chat khatam kar di.\n\n/start bhejo naya partner dhoondne ke liye.'
            )
        await update.message.reply_text('Chat khatam. /start bhejo dobara.')
        await remove_from_waiting(user_id)
    else:
        await remove_from_waiting(user_id)
        await update.message.reply_text('Aap kisi chat mein nahi ho. /start bhejo.')


async def skip_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    u = get_user(user_id)

    if not u['gender']:
        await update.message.reply_text('Pehle /start bhejo aur gender choose karo.')
        return

    if user_id in active_chats:
        partner_id = active_chats.pop(user_id, None)
        if partner_id:
            active_chats.pop(partner_id, None)
            await context.bot.send_message(
                chat_id=partner_id,
                text='⏭️ Partner ne skip kar diya. Naya partner dhoond rahe hain...'
            )
            waiting_users[get_user(partner_id)['gender']].append(partner_id)
            await find_chat_partner(partner_id, context)

        await update.message.reply_text('⏭️ Skip! Naya partner dhoond rahe hain...')
        waiting_users[u['gender']].append(user_id)
        await find_chat_partner(user_id, context)
    else:
        await remove_from_waiting(user_id)
        await update.message.reply_text('⏳ Naya partner dhoond rahe hain...')
        waiting_users[u['gender']].append(user_id)
        await find_chat_partner(user_id, context)


async def invite(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    u = get_user(user_id)

    bot_username = (await context.bot.get_me()).username
    invite_link = f"https://t.me/{bot_username}?start=ref_{user_id}"

    friends = u.get('referrals', 0)
    bonus_chats = u.get('bonus_chats', 0)

    await update.message.reply_text(
        f'👥 *Dost bulao — free chats pao!*\n\n'
        f'Aapka invite link:\n'
        f'`{invite_link}`\n\n'
        f'📊 Aapne ab tak *{friends}* dost bulaaye\n'
        f'🎁 Bonus chats: *{bonus_chats}*\n\n'
        f'*Rewards:*\n'
        f'• Har dost pe +5 free chats\n'
        f'• 3 dost pe 7 din Premium FREE\n'
        f'• 10 dost pe 30 din Premium FREE\n\n'
        f'👉 Neeche button se seedha WhatsApp/Telegram pe share karo:',
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "📤 WhatsApp pe share",
                url=f"https://wa.me/?text=Dekho%20ye%20bot!%20Anjaan%20logon%20se%20baat%20karo%20%E2%80%94%20{invite_link}"
            )],
            [InlineKeyboardButton(
                "📤 Telegram pe share",
                url=f"https://t.me/share/url?url={invite_link}&text=Mujhe%20is%20bot%20pe%20milte%20hain!"
            )],
        ])
    )


async def premium_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        '⭐ *Desi Anon Premium*\n\n'
        'Abhi sab kuch FREE hai! 🎉\n\n'
        'Jab hum bade honge, tab Premium features aayenge:\n'
        '• Unlimited chats\n'
        '• Priority in queue\n'
        '• Ad-free experience\n\n'
        'Filhaal — enjoy karo, doston ko bulao!',
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("👥 Invite karo", callback_data='show_invite')],
        ])
    )


async def show_invite(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    u = get_user(user_id)

    bot_username = (await context.bot.get_me()).username
    invite_link = f"https://t.me/{bot_username}?start=ref_{user_id}"

    friends = u.get('referrals', 0)

    await query.edit_message_text(
        f'👥 *Dost bulao!*\n\n'
        f'Aapka invite link:\n`{invite_link}`\n\n'
        f'📊 Aapne ab tak *{friends}* dost bulaaye',
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "📤 WhatsApp",
                url=f"https://wa.me/?text=Dekho%20ye%20bot!%20{invite_link}"
            )],
            [InlineKeyboardButton(
                "📤 Telegram",
                url=f"https://t.me/share/url?url={invite_link}&text=Anon%20chat%20bot!"
            )],
        ])
    )


async def buy_premium(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Пока отключено — включим, когда наберём аудиторию."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text('Abhi sab free hai! Enjoy karo 🎉')


async def pre_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.pre_checkout_query
    try:
        await query.answer(ok=True)
    except Exception as e:
        logging.error(f"Pre-checkout error: {e}")


async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    u = get_user(user_id)
    u['premium'] = True

    await update.message.reply_text(
        '🎉 *Premium activate ho gaya!*\n\n'
        'Dhanyavaad! Ab /start bhejo aur enjoy karo. 🎭',
        parse_mode='Markdown'
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    if user_id not in active_chats:
        await update.message.reply_text(
            '💬 Aap kisi se connected nahi ho.\n\n/start bhejo shuru karne ke liye.'
        )
        return

    partner_id = active_chats.get(user_id)
    if not partner_id:
        await update.message.reply_text('Partner nahi mila. /start bhejo.')
        return

    try:
        await update.message.copy(chat_id=partner_id)
    except Exception as e:
        logging.error(f"Ошибка пересылки: {e}")
        await update.message.reply_text('Message bhejne mein problem. /skip try karo.')


async def find_chat_partner(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    u = get_user(user_id)
    if not u['gender']:
        return

    user_gender = u['gender']
    opposite_gender = 'male' if user_gender == 'female' else 'female'

    if not waiting_users[opposite_gender]:
        await context.bot.send_message(
            chat_id=user_id,
            text='⏳ Abhi koi opposite gender wala available nahi hai.\n\nWait karo... jab koi aayega, hum connect kar denge.'
        )
        return

    partner_id = waiting_users[opposite_gender].pop(0)

    active_chats[user_id] = partner_id
    active_chats[partner_id] = user_id

    u['chats_today'] += 1
    u['total_chats'] += 1
    pu = get_user(partner_id)
    pu['chats_today'] += 1
    pu['total_chats'] += 1

    await context.bot.send_message(
        chat_id=user_id,
        text='✅ Partner mil gaya!\n\n'
             '💬 Message bhejo — text ya voice.\n'
             '⏭️ /skip — naya partner\n'
             '❌ /stop — chat khatam\n'
             '👥 /invite — dost bulao'
    )
    await context.bot.send_message(
        chat_id=partner_id,
        text='✅ Partner mil gaya!\n\n'
             '💬 Message bhejo — text ya voice.\n'
             '⏭️ /skip — naya partner\n'
             '❌ /stop — chat khatam\n'
             '👥 /invite — dost bulao'
    )


async def remove_from_waiting(user_id: int) -> None:
    u = get_user(user_id)
    gender = u.get('gender')
    if gender and user_id in waiting_users[gender]:
        waiting_users[gender].remove(user_id)


def main() -> None:
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('stop', stop_chat))
    application.add_handler(CommandHandler('skip', skip_chat))
    application.add_handler(CommandHandler('premium', premium_info))
    application.add_handler(CommandHandler('invite', invite))
    application.add_handler(CallbackQueryHandler(show_invite, pattern='^show_invite$'))
    application.add_handler(CallbackQueryHandler(buy_premium, pattern='^buy_premium$'))
    application.add_handler(CallbackQueryHandler(set_gender, pattern='^(male|female)$'))
    application.add_handler(PreCheckoutQueryHandler(pre_checkout))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    application.add_handler(MessageHandler(
        (filters.TEXT | filters.VOICE | filters.PHOTO | filters.VIDEO | filters.Sticker.ALL) & ~filters.COMMAND,
        handle_message
    ))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()