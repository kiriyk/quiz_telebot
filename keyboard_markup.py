from telebot.types import ReplyKeyboardMarkup, KeyboardButton

button_1 = 'Пройти квиз'
button_2 = 'Список победителей'

admin_buttons = ReplyKeyboardMarkup(row_width=2)
admin_buttons.add(KeyboardButton(button_1))
admin_buttons.add(KeyboardButton(button_2))
