import asyncio
from aiogram import Bot, Dispatcher, types
import logging
from aiogram.fsm.context import FSMContext
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
import requests


def get_food_info(product_name):
    url = f"https://world.openfoodfacts.org/cgi/search.pl?action=process&search_terms={product_name}&json=true"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        products = data.get('products', [])
        if products:  # Проверяем, есть ли найденные продукты
            first_product = products[0]
            return {
                'name': first_product.get('product_name', 'Неизвестно'),
                'calories': first_product.get('nutriments', {}).get('energy-kcal_100g', 0)
            }
        return None
    print(f"Ошибка: {response.status_code}")
    return None


class ProfileState(StatesGroup):
    weight = State()
    height = State()
    age = State()
    activity = State()
    city = State()
    calorie_goal = State()


class FoodState(StatesGroup):
    food_calories = State()


bd = {}
token = ""

bot = Bot(token=token)
dp = Dispatcher()

local_bd = {}


# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.reply("Добро пожаловать! Я ваш бот.")


@dp.message(Command("log_food"))
async def food_start(message: Message, state: FSMContext):
    try:
        print(message)
        product_name = message.text.split()[-1]
        await state.set_state(FoodState.food_calories)
        callories = get_food_info(product_name)['calories']
        await state.update_data(food_calories=callories)
        await message.reply("Укажите сколько грамм вы съели?")


    except Exception as e :
        print(e)
        await message.reply("Попробуйте ещё раз")


@dp.message(FoodState.food_calories)
async def process_weight(message: types.Message, state: FSMContext):
    try:
        gram = float(message.text)
        #print(state.get_data())
        data = await state.get_data()
        data = float(data['food_calories'])
        bd[message.from_user.id]['logged_calories'] += data * gram / 100
        await message.reply(f"Записано: {data * gram / 100}ккал.")
        await state.clear()
    except ValueError:
        await message.reply("Пожалуйста, введите число. Укажите граммовки :")


@dp.message(Command('log_water'))
async def cmd_set_profile(message: types.Message):
    try:

        bd[message.from_user.id]['logged_water'] += float(message.text.split()[-1])
        water_norm = bd[message.from_user.id]['water_goal'] - bd[message.from_user.id]['logged_water']

        if water_norm > 0:
            await message.reply(
                f"Количество выпитой воды успешно записано. Осталось для выполнения нормы: {water_norm}.")
        else:
            await message.reply(f"Количество выпитой воды успешно записано. Норма воды выполнена.")

    except ValueError as e:
        await message.reply("Пожалуйста, введите число. Количество выпитой вами воды ( в мл) :")


@dp.message(Command('log_workout'))
async def cmd_set_profile(message: types.Message):
    try:
        training = message.text.split()[-2]
        training_time = float(message.text.split()[-1])
        bd[message.from_user.id]['water_goal'] += training_time / 30 * 250
        bd[message.from_user.id]['burned_calories'] += training_time * 10

        await message.reply(
            f"Тернировака {training}, длительностью {training_time} минут'ы.Вы потратили {training_time * 10} ккал Дополнительно: выпейте {training_time / 30 * 250} мл воды.")

    except ValueError as e:
        await message.reply("Попробуйте ещё раз")


@dp.message(Command('check_progress'))
async def check_progress(message: types.Message):
    try:
        bot_answer = f"""📊 Прогресс:
        Вода:
        - Выпито: {bd[message.from_user.id]['logged_water']}  мл из {bd[message.from_user.id]['water_goal']} мл.
        - Осталось: {bd[message.from_user.id]['water_goal'] - bd[message.from_user.id]['logged_water']} мл.

        Калории:
        - Потреблено:
{bd[message.from_user.id]['logged_calories']} ккал из {bd[message.from_user.id]['calorie_goal']} ккал.
        - Сожжено: {bd[message.from_user.id]['burned_calories']} ккал.
        - Баланс: {bd[message.from_user.id]['calorie_goal'] - bd[message.from_user.id]['logged_calories'] + bd[message.from_user.id]['burned_calories']} ккал."""

        await message.reply(bot_answer)
    except Exception as e:
        await message.reply("Попробуйте ещё раз")


# Обработчик команды /help
@dp.message(Command('set_profile'))
async def cmd_set_profile(message: types.Message, state: FSMContext):
    await message.reply("Введите ваш вес (в кг):")
    await state.set_state(ProfileState.weight)


@dp.message(ProfileState.weight)
async def process_weight(message: types.Message, state: FSMContext):
    try:
        weight = float(message.text)
        await state.update_data(weight=weight)
        await message.reply("Введите ваш рост (в см):")
        await state.set_state(ProfileState.height)
    except ValueError:
        await message.reply("Пожалуйста, введите число. Введите ваш вес :")


@dp.message(ProfileState.height)
async def process_height(message: types.Message, state: FSMContext):
    try:
        height = float(message.text)
        await state.update_data(height=height)
        await message.reply("Введите ваш возраст :")
        await state.set_state(ProfileState.age)
    except ValueError:
        await message.reply("Пожалуйста, введите число. Введите ваш рост :")


@dp.message(ProfileState.age)
async def process_age(message: types.Message, state: FSMContext):
    try:
        age = float(message.text)
        await state.update_data(age=age)
        await message.reply("Сколько минут активности у вас в день? :")
        await state.set_state(ProfileState.activity)
    except ValueError:
        await message.reply("Пожалуйста, введите число. Введите ваш возраст :")


@dp.message(ProfileState.activity)
async def process_activity(message: types.Message, state: FSMContext):
    try:
        activity = float(message.text)
        await state.update_data(activity=activity)
        await message.reply("В каком городе вы находитесь? :")
        await state.set_state(ProfileState.city)
    except ValueError:
        await message.reply("Пожалуйста, введите число. Сколько минут активности у вас в день? :")


@dp.message(ProfileState.city)
async def process_city(message: Message, state: FSMContext):
    try:
        city = message.text
        await state.update_data(city=city)
        data = await state.get_data()
        bd[message.from_user.id] = data
        bd[message.from_user.id]['calorie_goal'] = bd[message.from_user.id]['weight'] * 10 + 6.25 * \
                                                   bd[message.from_user.id]['height'] - 5 * bd[message.from_user.id][
                                                       'age'] + bd[message.from_user.id]['activity'] * 8
        bd[message.from_user.id]['water_goal'] = bd[message.from_user.id]['weight'] * 20 + 500 * \
                                                 bd[message.from_user.id]['activity'] / 45 + 500
        bd[message.from_user.id]['logged_water'] = 0
        bd[message.from_user.id]['logged_calories'] = 0
        bd[message.from_user.id]['burned_calories'] = 0

        await state.set_state(ProfileState.calorie_goal)
        await message.reply(
            f"Укажите вашу цель по ккалориям, рекомендованное значение - {bd[message.from_user.id]['calorie_goal']}")
    except Exception as e:
        print(e)
        await message.reply("В каком городе вы находитесь? :")


@dp.message(ProfileState.calorie_goal)
async def calorie_goal(message: types.Message, state: FSMContext):
    try:
        calorie_goal = float(message.text)
        bd[message.from_user.id]['calorie_goal'] = calorie_goal
        await state.update_data(calorie_goal=calorie_goal)
        await state.clear()
        await message.reply("Результаты успешно записаны :")
    except ValueError:
        await message.reply(
            f"Укажите вашу цель по ккалориям, рекомендованное значение - {bd[message.from_user.id]['calorie_goal']}")


# Основная функция запуска бота
async def main():
    print("Бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
