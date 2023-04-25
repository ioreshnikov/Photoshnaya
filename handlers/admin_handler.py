from asyncio import sleep as async_sleep
from aiogram import types
from aiogram import Bot
from aiogram.types import InputMediaDocument, InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder
from utils.TelegramUserClass import TelegramDeserialize
from handlers.internal_logic.admin import i_set_theme
from handlers.internal_logic.on_join import i_on_user_join
from db.db_operations import ObjectFactory, RegisterDB, AdminDB, VoteDB
from utils.admin_keyboard import AdminKeyboard, CallbackManage, AdminActions

async def cmd_choose_group(message: types.Message, bot: Bot,
                           admin_unit: AdminDB, msg: dict):
    if not message.text:
        return
    user, _ = TelegramDeserialize.unpack(message)
    admin_right = await admin_unit.select_all_administrated_groups(user.telegram_id)

    if len(admin_right) == 0:
        await bot.send_message(user.telegram_id,
                               msg["admin"]["you_are_not_admin"])
        return

    builder = InlineKeyboardBuilder()
    data = CallbackManage(action=AdminActions.chosen_group,
                          group_id='-1')

    for admin in admin_right:
        data.group_id = admin[1]
        builder.button(text=f"{admin[0]}", callback_data=data.pack())

    builder.adjust(1, 1)

    await bot.send_message(user.telegram_id, msg["admin"]["choose_group"],
                           reply_markup=builder.as_markup())



async def callback_back(query: types.CallbackQuery, bot: Bot,
                        callback_data: CallbackManage, admin_unit: AdminDB,
                        msg: dict):
    admin_right = await admin_unit.select_all_administrated_groups(
            query.from_user.id
            )

    if not query.message:
        return
    if len(admin_right) == 0:
        await bot.send_message(query.from_user.id,
                               msg["admin"]["you_are_not_admin"])
        return

    builder = InlineKeyboardBuilder()
    data = callback_data
    data.action = AdminActions.chosen_group
    data.group_id = '-1'

    for admin in admin_right:
        data.group_id = admin[1]
        builder.button(text=f"{admin[0]}", callback_data=data.pack())

    builder.adjust(1, 1)

    await query.message.edit_text(text=msg["admin"]["choose_group"],
                                  reply_markup=builder.as_markup())



async def cmd_action_choose(query: types.CallbackQuery, bot: Bot,
                            callback_data: CallbackManage,
                            admin_unit: AdminDB, msg: dict):

    bot_name = await bot.me()
    if not query.message or not bot_name.username:
        return
    keyboard = AdminKeyboard.fromcallback(callback_data)
    vote_in_progress = await admin_unit.get_current_vote_status(
            int(callback_data.group_id)
            )

    if not vote_in_progress:
        keyboard_r = keyboard.keyboard_no_vote
    else:
        keyboard_r = keyboard.keyboard_vote_in_progress

    status = await admin_unit.get_info(int(callback_data.group_id))
    info = ''
    if len(status) == 1:
        info = f"Текущая тема: {status[0]}\n"
    elif len(status) == 2:
        link_vote = ObjectFactory.build_vote_link(bot_name.username,
                                                  callback_data.group_id)
        info = (f"Текущая тема: {status[0]}\n"
                f"Количество проголосовавших: <b>{status[1]}</b>\n"
                f"Ссылка на голосование: {link_vote}\n")
    elif len(status) == 3:
        info = (f"Текущая тема: {status[0]}\n"
                f"Количество проголосовавших: {status[1]}\n"
                "Ссылка на голосование ")
    caption = info + '\n' + msg["admin"]["choose_action"]
    await query.message.edit_text(text=caption,
                                  reply_markup=keyboard_r,
                                  parse_mode="HTML")


async def cmd_check_if_sure(query: types.CallbackQuery,
                            callback_data: CallbackManage, msg: dict):
    if not query.message:
        return
    keyboard = AdminKeyboard.fromcallback(callback_data)
    await query.message.edit_text(text=msg["admin"]["are_you_sure_F"],
                                  reply_markup=keyboard.keyboard_are_you_sure)


async def cmd_check_if_sure_vote(query: types.CallbackQuery,
                                 callback_data: CallbackManage, msg: dict):
    if not query.message:
        return
    keyboard = AdminKeyboard.fromcallback(callback_data)
    await query.message.edit_text(text=msg["admin"]["are_you_sure_S"],
                                  reply_markup=keyboard.keyboard_are_you_sure_start)


async def cmd_finish_contest(query: types.CallbackQuery, bot: Bot,
                             callback_data: CallbackManage,
                             admin_unit: AdminDB, msg: dict):
    if not query.message:
        return
    keyboard = AdminKeyboard.fromcallback(callback_data)
    bot_t = await bot.me()
    if not bot_t.username:
        await query.message.edit_text(text=msg["vote"]["no_username_bot"],
                                  reply_markup=keyboard.keyboard_back)
        return

    bot_link = ObjectFactory.build_vote_link(bot_t.username, callback_data.group_id)
    message = msg["vote"]["vote_started"] + f" {bot_link}"
    await admin_unit.change_current_vote_status(int(callback_data.group_id))
    await query.message.edit_text(text=message,
                              reply_markup=keyboard.keyboard_back)


async def cmd_finish_vote(query: types.CallbackQuery, bot: Bot,
                          callback_data: CallbackManage, admin_unit: AdminDB,
                          msg: dict):
    if not query.message:
        return
    await admin_unit.change_current_vote_status(int(callback_data.group_id))
    keyboard = AdminKeyboard.fromcallback(callback_data)
    vote = VoteDB(admin_unit.engine)


    ids = await admin_unit.select_contest_photos_ids_and_types(
            int(callback_data.group_id))
    if len(ids) == 0:
        await query.message.edit_text(text=msg["admin"]["no_photos_at_end"],
                              reply_markup=keyboard.keyboard_back)
        return

    id, user = await vote.select_winner_from_contest(int(callback_data.group_id))
    if not user:
        await query.message.edit_text(text=msg["admin"]["no_winner"],
                              reply_markup=keyboard.keyboard_back)
        return

    file_id = await vote.select_file_id(id)
    likes = await vote.select_all_likes_file_id(int(callback_data.group_id), file_id)
    type_photo = await vote.select_file_type_by_file_id(file_id)
    await query.message.edit_text(text=msg["admin"]["vote_end"],
                          reply_markup=keyboard.keyboard_back)

    user_info = f"Победитель: @{user[0]}, {user[1]}\nЛайков: {likes}"
    if type_photo == 'photo':
        await bot.send_photo(chat_id=query.from_user.id, photo=file_id,
                             caption=user_info)
    else:
        await bot.send_document(chat_id=query.from_user.id, document=file_id,
                                caption=user_info)
    ids = await admin_unit.select_contest_photos_ids_and_types(
            int(callback_data.group_id))
    if len(ids) == 0:
        return
    await internal_view_submissions(query.from_user.id, ids,
                                    bot, admin_unit, callback_data)
    await vote.erase_all_photos(int(callback_data.group_id))
    await admin_unit.change_contest_to_none(int(callback_data.group_id))



async def view_votes(query: types.CallbackQuery, bot: Bot,
                     callback_data: CallbackManage, admin_unit: AdminDB):
    ids = await admin_unit.select_contest_photos_ids_and_types(
            int(callback_data.group_id))
    await internal_view_submissions(query.from_user.id, ids,
                                    bot, admin_unit, callback_data)


async def view_submissions(query: types.CallbackQuery, bot: Bot,
                           callback_data: CallbackManage, admin_unit: AdminDB):

    ids = await admin_unit.select_contest_photos_ids_and_types(
            int(callback_data.group_id))
    if len(ids) == 0:
        return
    await internal_view_submissions(query.from_user.id, ids, bot, admin_unit,
                                    callback_data)


async def internal_view_submissions(chat_id: int, ids: list, bot: Bot,
                                    admin_unit: AdminDB,
                                    callback_data: CallbackManage):
    group_id = int(callback_data.group_id)
    if len(ids) == 1:
        if ids[0][1] == 'photo':
            await bot.send_photo(chat_id=chat_id, photo=ids[0][0])
        else:
            await bot.send_document(chat_id=chat_id, document=ids[0][0])
        return

    MAX_SUBMISSIONS = 10
    submissions_photos = []
    submissions_docs = []
    vote = VoteDB(admin_unit.engine)
    for id in ids:
        media_type, media = id[1], id[0]
        if media_type == 'photo':
            submissions_photos.append(InputMediaPhoto(type='photo',
                                                      media=media))
        else:
            submissions_docs.append(InputMediaDocument(type='document',
                                                       media=media))

        if len(submissions_photos) == MAX_SUBMISSIONS:
            await send_photos(submissions_photos, bot, chat_id)
            await send_possible_caption(submissions_photos,
                                        group_id,
                                        bot, vote, chat_id)
            submissions_photos.clear()
        if len(submissions_docs) == MAX_SUBMISSIONS:
            await send_photos(submissions_docs, bot, chat_id)
            await send_possible_caption(submissions_docs,
                                        group_id,
                                        bot, vote, chat_id)
            submissions_docs.clear()

    if submissions_photos:
        await send_photos(submissions_photos,  bot, chat_id)
        await send_possible_caption(submissions_photos,
                                        group_id,
                                    bot, vote, chat_id)
    if submissions_docs:
        await send_photos(submissions_docs, bot, chat_id)
        await send_possible_caption(submissions_docs,
                                        group_id,
                                    bot, vote, chat_id)

    del submissions_photos
    del submissions_docs

async def send_possible_caption(submissions: list,
                                group_id: int,
                                bot: Bot, vote: VoteDB,
                                chat_id: int):
    caption = ''
    i = 1
    for obj in submissions:
        if not isinstance(obj.media, str):
            continue
        likes, user = await vote.select_all_likes_with_user(group_id,
                                                      obj.media)
        if len(user) < 2:
            continue
        if likes is None:
            likes = 0
        caption += f"{i}) Лайков = {likes}, @{user[0]}, {user[1]}, {user[2]}\n"
        i += 1
    if caption:
        await bot.send_message(chat_id=chat_id, text=caption)


async def send_photos(list_of_object: list[InputMediaDocument
                                               | InputMediaPhoto],
                          bot: Bot, msg: int):
    if len(list_of_object) == 0:
        return
    if len(list_of_object) > 1:
        await bot.send_media_group(chat_id=msg, media=list_of_object)
    elif len(list_of_object) == 1 and isinstance(list_of_object[0],
                                                 InputMediaDocument):
        await bot.send_document(chat_id=msg, document=list_of_object[0].media)
    elif len(list_of_object) == 1 and isinstance(list_of_object[0],
                                                 InputMediaPhoto):
        await bot.send_photo(chat_id=msg, photo=list_of_object[0].media)
    await async_sleep(0.5)


async def set_theme(message: types.Message, bot: Bot, admin_unit: AdminDB):
    if not message.text or not message.from_user:
        return
    user, chat = TelegramDeserialize.unpack(message)
    admin_right = await admin_unit.check_admin(user.telegram_id, chat.telegram_id)
    if admin_right is False:
        return

    user_theme = message.text.split()
    msg = await i_set_theme(user_theme, admin_unit, chat)
    await bot.send_message(message.chat.id, msg)



async def on_user_join(message: types.Message, bot: Bot,
                       register_unit: RegisterDB):
    user, chat = TelegramDeserialize.unpack(message,
                                            message_id_not_exists=True)

    msg, reg_msg = await i_on_user_join(register_unit=register_unit,
                                  user=user, chat=chat)

    await bot.send_message(chat.telegram_id, msg)
    if reg_msg:
        await bot.send_message(chat.telegram_id, reg_msg)
