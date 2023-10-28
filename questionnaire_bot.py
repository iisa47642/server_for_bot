from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, State, StatesGroup
from aiogram.fsm.storage.redis import RedisStorage, Redis
from aiogram.types import (Message, CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, PhotoSize)
from config import Config, load_config

redis = Redis(host='localhost')
storage = RedisStorage(redis=redis)
config: Config = load_config('/Users/Isa/Desktop/FSM/.env')

bot = Bot(config.tg_bot.token)
dp = Dispatcher(storage=storage)

user_dict: dict[int, dict[str, str | bool | int]] = {}


class FSMFillForm(StatesGroup):
    fill_name = State()
    fill_age = State()
    fill_gender = State()
    fill_photo = State()
    fill_education = State()
    fill_wish_news = State()


@dp.message(CommandStart(), StateFilter(default_state))
async def process_start_command(message: Message):
    await message.answer(
        text='Этот бот демонстрирует работу FSM\n\n'
             'Чтобы перейти к заполнению анкеты - '
             'отправьте команду /fillform')


@dp.message(Command(commands='cancel'), StateFilter(default_state))
async def process_cancel_command(message: Message):
    await message.answer(
        text='Отменять нечего. Вы вне машины состояний\n\n'
             'Чтобы перейти к заполнению анкеты - '
             'отправьте команду /fillform'
    )


@dp.message(Command(commands='cancel'), ~StateFilter(default_state))
async def process_cancel_command_state(message: Message, state: FSMContext):
    await message.answer(
        text='Вы вышли из машины состояний\n\n'
             'Чтобы снова перейти к заполнению анкеты - '
             'отправьте команду /fillform'
    )
    await state.clear()


@dp.message(Command(commands='fillform'), StateFilter(default_state))
async def process_fillform_command(message: Message, state: FSMContext):
    await message.answer(text='Пожалуйста, введите ваше имя')
    await state.set_state(FSMFillForm.fill_name)


@dp.message(StateFilter(FSMFillForm.fill_name), F.text.isalpha())
async def process_name_sent(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(text='Спасибо!\n\nА теперь введите ваш возраст')
    await state.set_state(FSMFillForm.fill_age)


@dp.message(StateFilter(FSMFillForm.fill_name))
async def warning_not_name(message: Message):
    await message.answer(
        text='То, что вы отправили не похоже на имя\n\n'
             'Пожалуйста, введите ваше имя\n\n'
             'Если вы хотите прервать заполнение анкеты - '
             'отправьте команду /cancel')


@dp.message(StateFilter(FSMFillForm.fill_age),
            lambda x: x.text.isdigit() and 4 <= int(x.text) <= 120)
async def process_age_sent(message: Message, state: FSMContext):
    await state.update_data(age=int(message.text))
    male_button = InlineKeyboardButton(
        text='Мужской ♂',
        callback_data='male'
    )
    female_button = InlineKeyboardButton(
        text='Женский ♀',
        callback_data='female'
    )
    undefined_button = InlineKeyboardButton(
        text='🤷 Пока не ясно',
        callback_data='undefined_gender'
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[male_button, female_button],
                         [undefined_button]])
    await message.answer(text='Спасибо!\n\nУкажите ваш пол',
                         reply_markup=keyboard)
    await state.set_state(FSMFillForm.fill_gender)


@dp.message(StateFilter(FSMFillForm.fill_age))
async def warning_not_age(message: Message):
    await message.answer(
        text='Возраст должен быть целым числом от 4 до 120\n\n'
             'Попробуйте еще раз\n\nЕсли вы хотите прервать '
             'заполнение анкеты - отправьте команду /cancel'
    )


@dp.callback_query(StateFilter(FSMFillForm.fill_gender),
                   F.data.in_(['male', 'female', 'undefined_gender']))
async def process_gender_press(callback: CallbackQuery, state: FSMContext):
    await state.update_data(gender=callback.data)
    await callback.message.delete()
    await callback.message.answer(
        text='Спасибо! А теперь загрузите, пожалуйста, ваше фото'
    )
    await state.set_state(FSMFillForm.fill_photo)


@dp.message(StateFilter(FSMFillForm.fill_photo),
            F.photo[-1].as_('largest_photo'))
async def process_photo_sent(message: Message,
                             state: FSMContext,
                             largest_photo: PhotoSize):

    await state.update_data(
        photo_unique_id=largest_photo.file_unique_id,
        photo_id=largest_photo.file_id
    )
    secondary_button = InlineKeyboardButton(
        text='Среднее',
        callback_data='secondary'
    )
    higher_button = InlineKeyboardButton(
        text='Высшее',
        callback_data='higher'
    )
    no_edu_button = InlineKeyboardButton(
        text='Нету',
        callback_data='no_edu'
    )
    keyboard: list[list[InlineKeyboardButton]] = InlineKeyboardMarkup(
        inline_keyboard=[[secondary_button, higher_button],
                         [no_edu_button]]
    )
    await message.answer(
        text='Спасибо!\n\nУкажите ваше образование',
        reply_markup=keyboard
    )
    await state.set_state(FSMFillForm.fill_education)


@dp.message(StateFilter(FSMFillForm.fill_photo))
async def warning_not_photo(message: Message):
    await message.answer(
        text='Пожалуйста, на этом шаге отправьте '
             'ваше фото\n\nЕсли вы хотите прервать '
             'заполнение анкеты - отправьте команду /cancel'
    )


@dp.callback_query(StateFilter(FSMFillForm.fill_education),
                   F.data.in_(['secondary', 'higher', 'no_edu']))
async def process_education_press(callback: CallbackQuery, state: FSMContext):
    await state.update_data(education=callback.data)
    yes_news = InlineKeyboardButton(
        text='Да',
        callback_data='yes_news'
    )
    no_news = InlineKeyboardButton(
        text='Нет, спасибо',
        callback_data='no_news'
    )
    keyboard: list[list[InlineKeyboardButton]] = InlineKeyboardMarkup(
        inline_keyboard=[[yes_news, no_news]]
    )
    await callback.message.answer(
        text='Спасибо!\n\nОстался последний шаг.\n'
             'Хотели бы вы получать новости?',
        reply_markup=keyboard
    )
    await state.set_state(FSMFillForm.fill_wish_news)


@dp.callback_query(StateFilter(FSMFillForm.fill_wish_news),
                   F.data.in_(['yes_news', 'no_news']))
async def process_wish_news_press(callback: CallbackQuery, state: FSMContext):
    await state.update_data(wish_news=callback.data == 'yes_news')
    user_dict[callback.from_user.id] = await state.get_data()
    await state.clear()
    await callback.message.edit_text(
        text='Спасибо! Ваши данные сохранены!\n\n'
             'Вы вышли из машины состояний'
    )
    await callback.message.answer(
        text='Чтобы посмотреть данные вашей '
             'анкеты - отправьте команду /showdata'
    )


@dp.message(StateFilter(default_state), Command(commands='showdata'))
async def process_showdata_command(message: Message):
    if user_dict[message.from_user.id]:
        await message.answer_photo(
            photo=user_dict[message.from_user.id]['photo_id'],
            caption=f'Имя: {user_dict[message.from_user.id]["name"]}\n'
                    f'Возраст: {user_dict[message.from_user.id]["age"]}\n'
                    f'Пол: {user_dict[message.from_user.id]["gender"]}\n'
                    f'Образование: {user_dict[message.from_user.id]["education"]}\n'
                    f'Получать новости: {user_dict[message.from_user.id]["wish_news"]}'
        )
    else:
        message.answer(
            text='Вы еще не заполняли анкету. Чтобы приступить - '
            'отправьте команду /fillform'
        )


@dp.message(StateFilter(default_state))
async def send_echo(message: Message):
    await message.reply(text='Извините, моя твоя не понимать')

if __name__ == '__main__':
    dp.run_polling(bot)
