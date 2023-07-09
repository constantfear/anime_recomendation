from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils.markdown import link
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import sqlite3
import pickle
import config as cfg
import buttons as btn


class Recomendation(StatesGroup):
    recomendation = State()
    reg = State()
    show_recs = State()
    get_rating = State()


con = sqlite3.connect(cfg.db_path)
cur = con.cursor()

with open(cfg.recs, 'rb') as file:
    recs = pickle.load(file)

bot = Bot(token=cfg.TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


async def get_recomendation(title):
    try:
        querry = f"SELECT id FROM anime WHERE Title='{title}'"
        cur.execute(querry)
        idx = cur.fetchall()[0][0] - 1
        sim_scores = list(enumerate(recs[idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        sim_scores = sim_scores[1:300]
        movie_indices = [i[0]+1 for i in sim_scores]
        return movie_indices
    except Exception as ex:
        print(ex)
        return 0
    

@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await message.reply("Привет!\nЯ бот, который может порекомендовать тебе похожие аниме, на основе твоего запроса")
    querry = f"SELECT * FROM users WHERE user_tg_id = {message.from_user.id}"
    try:
        cur.execute(querry)
        i = cur.fetchall()
        if len(i)==0:
            await bot.send_message(message.from_user.id, "Для того чтобы начать пользоваться ботом, введите ваш возраст")
            await Recomendation.reg.set()
        else:
            await bot.send_message(message.from_user.id, "Для получения рекомендации введите команду /anime")
        print(i)
    except Exception as ex:
        await bot.send_message(message.from_user.id, "ОЙ, произошла ошибка ):")
        print(ex)
    

@dp.message_handler(state = Recomendation.reg)
async def dowload(message: types.Message, state: FSMContext):
    try:
        data = (message.from_user.id, message.from_user.username, int(message.text))
        querry = "INSERT INTO users(user_tg_id, user_name, age) VALUES (" + ','.join(['?'] * len(data)) + ')'
        cur.execute(querry, data)
        con.commit()
        await bot.send_message(message.from_user.id, "Для получения рекомендации введите команду /anime")    
        await state.finish()
    except Exception as ex:
        print(ex)
        await bot.send_message(message.from_user.id, "ОЙ, произошла ошибка ):")


@dp.message_handler(commands=['help'])
async def process_help_command(message: types.Message):
    await message.reply("Привет!\nЯ бот, который может порекомендовать тебе похожие аниме, на основе твоего запроса.\nДля получения рекомендации введите команду /anime")
    

@dp.message_handler(commands=['anime'])
async def process_photo_command(message: types.Message):
    querry = f"SELECT * FROM users WHERE user_tg_id = {message.from_user.id}"
    try:
        cur.execute(querry)
        i = cur.fetchall()
        if len(i)==0:
            await bot.send_message(message.from_user.id, "Для того чтобы начать пользоваться ботом, введите ваш возраст")
            await Recomendation.reg.set()
        else:
            await message.answer(text=f"Привет, {message.from_user.full_name}, напиши мне название аниме, и я попробую предложить тебе похожие.")
            await Recomendation.recomendation.set()
        print(i)
    except Exception as ex:
        await bot.send_message(message.from_user.id, "ОЙ, произошла ошибка ):")
        print(ex)
    

@dp.message_handler(state = Recomendation.recomendation)
async def dowload(message: types.Message, state: FSMContext):
    rec_indices = await get_recomendation(message.text)
    if not(rec_indices):
        await bot.send_message(message.from_user.id, "Я не знаю такого аниме( \n Возможно в названии есть ошибка")
        await state.finish()
    else:
        id = rec_indices[0]
        querry = f"SELECT Poster, Title, Url FROM anime WHERE id='{id}'"
        cur.execute(querry)
        d= cur.fetchall()

        POSTER = d[0][0]
        inline_btn_1 = types.InlineKeyboardButton('Смотреть', url=d[0][2])
        inline_kb1 = types.InlineKeyboardMarkup().add(inline_btn_1)
        await message.answer(text="Нашлось несколько схожих аниме!", reply_markup = btn.recs)
        await bot.send_photo(message.from_user.id, POSTER, caption=d[0][1], reply_markup = inline_kb1)
        await state.update_data(movies_id = rec_indices)
        await state.update_data(cur_id = 0)
        await Recomendation.show_recs.set()


@dp.message_handler(state = Recomendation.show_recs)
async def dowload(message: types.Message, state: FSMContext):
    text = message.text
    data = await state.get_data()
    rec_indices = data['movies_id']
    cur_id = data['cur_id']
    if text == "Не интересно":
        cur_id += 1
        querry = f"SELECT Poster, Title, Url FROM anime WHERE id='{rec_indices[cur_id]}'"
        cur.execute(querry)
        d= cur.fetchall()
        POSTER = d[0][0]
        inline_btn_1 = types.InlineKeyboardButton('Смотреть', url=d[0][2])
        inline_kb1 = types.InlineKeyboardMarkup().add(inline_btn_1)
        await bot.send_photo(message.from_user.id, POSTER, caption=d[0][1], reply_markup = inline_kb1)
        await state.update_data(cur_id = cur_id)
    elif text == "Ввести другое аниме":
        await message.answer(text=f"Напишите мне название аниме, и я попробую предложить похожие.", reply_markup=btn.empty_keyboard)
        await Recomendation.recomendation.set()
    elif text == "Отмена":
        await bot.send_message(message.from_user.id, "Отменяем", reply_markup=btn.empty_keyboard)
        await state.finish()
    else:
        await bot.send_message(message.from_user.id, "Неизвестная команда, попробуйте еще раз", reply_markup=btn.recs)

@dp.message_handler()
async def echo_message(msg: types.Message):
    await msg.reply("Для получения рекомендации введите команду /anime")



if __name__ == '__main__':
    executor.start_polling(dp)