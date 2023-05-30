import telebot
import requests
from bs4 import BeautifulSoup as bs
from decouple import config
import datetime
from telebot import types
import time

BOT_TOKEN = config('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)


@bot.message_handler(commands=['start'])
def start_message(message):
    global ls
    bot.send_chat_action(message.chat.id, 'typing')
    time.sleep(1)
    bot.send_message(message, "Loading...⏳", reply_markup=types.ReplyKeyboardRemove())
    ls = []
    date = datetime.datetime.now().date()
    while True:
        url = f'https://kaktus.media/?lable=8&date={date}&order=time'
        response = requests.get(url).text
        page = bs(response, 'lxml')
        divs = page.find_all('div', 'ArticleItem--data ArticleItem--data--withImage')
        link = page.find_all('a', 'ArticleItem--name')
        if len(divs) < 20:
            for i in range(len(divs)):
                new = bs(requests.get(link[i].get('href')).text, 'lxml')
                ps = new.find_all('p')
                ls.append(
                    [
                        divs[i].find('a', 'ArticleItem--name').text.replace('\n', ''),
                        divs[i].find('img').get('src')
                        if divs[i].find('img') != None
                        else 'None',
                        ' '.join([i.text.strip() if i != None else 'None' for i in ps]),
                    ]
                )
        if len(divs) >= 20:
            for i in range(len(divs[: 20 - len(ls)])):
                new = bs(requests.get(link[i].get('href')).text, 'lxml')
                ps = new.find_all('p')
                ls.append(
                    [
                        divs[i].find('a', 'ArticleItem--name').text.replace('\n', ''),
                        divs[i].find('img').get('src')
                        if divs[i].find('img') != None
                        else 'None',
                        ' '.join([i.text.strip() if i != None else 'None' for i in ps]),
                    ]
                )
        if len(ls) < 20:
            date -= datetime.timedelta(days=1)
        else:
            break
    for i in range(len(ls)):
        ls[i].insert(0, str(i + 1))
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    bt1 = types.KeyboardButton('News')
    bt2 = types.KeyboardButton('Quit')
    markup.add(bt1, bt2)
    bot.send_message(
        message.chat.id, 'Press News to get the latest 20 news', reply_markup=markup
    )


@bot.message_handler(func=lambda x: x.text in ['News', 'Quit'])
def bts(message):
    if message.text == 'News':
        n_markup = types.ReplyKeyboardMarkup(row_width=5, resize_keyboard=True)
        btns = [types.KeyboardButton(str(i + 1)) for i in range(20)]
        n_markup.add(*btns)
        bot.send_message(
            message.from_user.id, 'Choose news by number(1-20)', reply_markup=n_markup
        )
        for i in range(len(ls)):
            bot.send_message(message.from_user.id, ls[i][0] + '.' + ls[i][1])
    elif message.text == 'Quit':
        bot.send_message(
            message.from_user.id, 'Farewell', reply_markup=types.ReplyKeyboardRemove()
        )


@bot.message_handler(func=lambda message: message.text.isdigit())
def handle_news_selection(message):
    global selected_news_id
    last_markup = types.ReplyKeyboardMarkup(row_width=2)
    bt1 = types.KeyboardButton('Description')
    bt2 = types.KeyboardButton('Photo')
    last_markup.add(bt1, bt2)
    selected_news_id = int(message.text)
    if selected_news_id > 0 and selected_news_id <= 20:
        selected_news = ls[selected_news_id - 1][1]
        bot.send_message(
            message.from_user.id,
            f'You chose {selected_news_id}:\n{selected_news}',
            reply_markup=last_markup,
        )


@bot.message_handler(func=lambda x: x.text in ['Description', 'Photo'])
def des_photo(message):
    option_markup = types.ReplyKeyboardMarkup(row_width=2)
    bt1 = types.KeyboardButton('Y')
    bt2 = types.KeyboardButton('N')
    option_markup.add(bt1, bt2)
    if message.text == 'Description':
        bot.send_message(
            message.chat.id,
            ls[selected_news_id - 1][3],
            reply_markup=types.ReplyKeyboardRemove(),
        )
    elif message.text == 'Photo':
        bot.send_photo(
            message.from_user.id,
            ls[selected_news_id - 1][2],
            reply_markup=types.ReplyKeyboardRemove(),
        )
    bot.send_message(
        message.from_user.id, 'Wanna continue?(y/n)', reply_markup=option_markup
    )


@bot.message_handler(func=lambda x: x.text.lower() in ['y', 'n'])
def y_n(message):
    if message.text.lower() == 'y':
        start_message(message)
    elif message.text.lower() == 'n':
        bot.send_message(
            message.from_user.id, "Farewell", reply_markup=types.ReplyKeyboardRemove()
        )


bot.polling()
