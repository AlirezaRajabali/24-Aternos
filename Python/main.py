from configparser import ConfigParser
from javascript import require, On
import threading, os
from sys import platform
from flask import Flask  # افزوده‌شده برای UptimeRobot

mineflayer = require('mineflayer')

### By Fortcote
### https://discord.gg/bjgpVAxgyE

# --- تنظیمات Flask برای UptimeRobot ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running"

def run_flask():
    app.run(host="0.0.0.0", port=8080)  # پورت 8080 معمولاً در Render مجازه

threading.Thread(target=run_flask).start()  # اجرای Flask در ترد جداگانه

# --- تنظیمات کانفیگ ---
config = ConfigParser()

config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
print(f"Reading config from: {config_path}")

config.read(config_path)
print("Config sections:", config.sections())

# --- راه‌اندازی بات ماین‌کرفت ---
def started(stop):
    bot = mineflayer.createBot({
        'host': config.get('server', 'host'),
        'port': int(config.get('server', 'port')),
        'username': config.get('bot', 'name')
    })
    print('Start')

    @On(bot, "login")
    def login(this):
        bot.chat(config.get('bot', 'register'))
        bot.chat(config.get('bot', 'login'))
        print("Bot online")

    @On(bot, "error")
    def error(err, *a):
        print("Connect ERROR: ", err, a)

    @On(bot, "kicked")
    def kicked(this, reason, *a):
        print("I was kicked: ", reason, a)
        print('Reconnecting...')
        bot.end(); bot.join()

    @On(bot, "chat")
    def handle(this, username, message, *args):
        if username == bot.username:
            return
        elif message.startswith(config.get('command', 'position')):
            p = bot.entity.position
            bot.chat(f"Bot > I am at {p.toString()}")
        elif message.startswith(config.get('command', 'start')):
            bot.chat('24 ATERNOS > Bot started! - Made By Fortcote')
            bot.setControlState('forward', True)
            bot.setControlState('jump', True)
            bot.setControlState('sprint', True)
        elif message.startswith(config.get('command', 'stop')):
            bot.chat('24 ATERNOS > Bot stoped! - Made By Fortcote')
            bot.clearControlStates()

    @On(bot, "spawn")
    def spawn(this):
        bot.chat("Bot > Spawned!")

    @On(bot, "death")
    def death(this):
        bot.chat("Bot > Respawn!")

def start():
    global bott, stop_threads
    stop_threads = False
    bott = threading.Thread(target=started, args=(lambda: stop_threads,))
    bott.start()

def stop():
    try:
        if platform == "win32":
            os.system('taskkill /f /im node.exe')
        else:
            os.system('killall node')
        print("Bot offline")
    except:
        pass

if __name__ == '__main__':
    start()
