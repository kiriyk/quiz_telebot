from telebot.async_telebot import AsyncTeleBot
from telebot import types
import asyncio

from settings import BOT_TOKEN, ADMIN_ID
from quiz_options import quiz_questions, greeting_message, result_messages, help_message, admin_message
from keyboard_markup import admin_buttons, button_1, button_2

from db import add_user, get_users


class TelebotQuiz:
    def __init__(self):
        self.bot = AsyncTeleBot(BOT_TOKEN)
        self.winners = {}
        self.timers = {}

    def bot_run(self):
        self.bot.register_message_handler(self.handle_start, commands=['start'])
        self.bot.register_message_handler(self.help_command, commands=['help'])
        self.bot.register_message_handler(self.handle_answer, func=lambda message: True)

        print('Bot is running')
        asyncio.run(self.bot.infinity_polling())

    async def handle_start(self, message, admin=True):
        if message.chat.id == ADMIN_ID and admin is True:
            await self.bot.send_message(message.chat.id, admin_message.format(message.chat.username),
                                        reply_markup=admin_buttons)
        else:
            await self.bot.send_message(message.chat.id, greeting_message.format(message.chat.username,
                                                                                 str(len(quiz_questions))))
            self.winners.update({f'{message.chat.username}': [0, 0]})
            await asyncio.sleep(3)
            task = asyncio.create_task(self.start_quiz(message, 0))
            await task

    async def start_quiz(self, message, question_index):
        if question_index < len(quiz_questions):
            question_data = quiz_questions[question_index]
            question = question_data['question']
            options = question_data['options']

            keyboard = types.ReplyKeyboardMarkup(row_width=2)
            for option in options:
                keyboard.add(types.KeyboardButton(option))

            if question_data.get('url'):
                video = open(question_data.get('url'), 'rb')
                await self.bot.send_video(message.chat.id, video)

            message = await self.bot.send_message(message.chat.id, question, reply_markup=keyboard)

            timer = asyncio.create_task(self.question_timer(message))
            self.timers[f'{message.chat.id}'] = timer
            await timer
        else:
            task = asyncio.create_task(self.send_quiz_result(message))
            await task

    async def handle_answer(self, message):
        if message.chat.id == ADMIN_ID and (message.text == button_1 or message.text == button_2):
            if message.text == button_1:
                await self.handle_start(message, admin=False)
            elif message.text == button_2:
                await self.send_winners(message)
        else:
            question_idx = self.winners.get(f'{message.chat.username}')[0]
            if str(message.chat.id) in self.timers:
                self.timers[str(message.chat.id)].cancel()
                del self.timers[str(message.chat.id)]

            question_data = quiz_questions[question_idx]
            answer_index = question_data['answer']

            if message.text == question_data['options'][answer_index]:
                self.winners[f'{message.chat.username}'][1] += 1
                await self.bot.send_message(message.chat.id, 'Правильно!')
            else:
                await self.bot.send_message(message.chat.id, 'Неправильно!')

            self.winners[f'{message.chat.username}'][0] += 1

            task = asyncio.create_task(self.start_quiz(message, question_idx + 1))
            await task

    async def send_quiz_result(self, message):
        if self.winners.get(f'{message.chat.username}')[1] == len(quiz_questions):
            result_message = result_messages[0]
            add_user(message.chat.username)
            self.get_winners_list()
        elif self.winners.get(f'{message.chat.username}')[1] == len(quiz_questions) - 1:
            result_message = result_messages[1]
        else:
            result_message = result_messages[2]

        del self.winners[f'{message.chat.username}']
        self.get_winners_list()

        await self.bot.send_message(message.chat.id, result_message, reply_markup=types.ReplyKeyboardRemove())

    async def question_timer(self, message):
        try:
            await asyncio.sleep(quiz_questions[self.winners[f'{message.chat.username}'][0]]['timer'])
            await self.bot.send_message(message.chat.id, 'Время вышло, переходим к следующему вопросу!')
            self.winners[f'{message.chat.username}'][0] += 1
            await self.start_quiz(message, self.winners[f'{message.chat.username}'][0])
        except asyncio.CancelledError:
            pass

    async def help_command(self, message):
        await self.bot.send_message(message.chat.id, help_message)

    async def send_winners(self, message):
        users = get_users()
        users_list = [f'{user.id}. {user.username} - Completed quiz at {user.created_at}\n' for user in users]
        result = ''.join(users_list)
        await self.bot.send_message(message.chat.id, result, reply_markup=types.ReplyKeyboardRemove())

    @staticmethod
    def get_winners_list():
        users = get_users()
        with open('winner.txt', 'w', encoding='UTF-8') as file:
            for user in users:
                string = f'{user.id}. {user.username} - Completed quiz at {user.created_at}\n'
                file.write(string)


if __name__ == '__main__':
    bot = TelebotQuiz()
    bot.bot_run()
