from configparser import ConfigParser
from javascript import require, On
import threading, os, time
from sys import platform
from flask import Flask
import _thread

mineflayer = require('mineflayer')

config = ConfigParser()
config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
config.read(config_path)

print("Reading config from:", config_path)
print("Config sections:", config.sections())

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def start_bot():
    while True:
        try:
            bot = mineflayer.createBot({
                'host': config.get('server', 'host'),
                'port': int(config.get('server', 'port')),
                'username': config.get('bot', 'name')
            })

            print("Bot starting...")

            @On(bot, "login")
            def login(this):
                bot.chat(config.get('bot', 'register'))
                bot.chat(config.get('bot', 'login'))
                print("Bot logged in.")

            @On(bot, "error")
            def error(err, *a):
                print("Connect ERROR:", err)

            @On(bot, "kicked")
            def kicked(this, reason, *a):
                print("I was kicked:", reason)
                bot.end()

            @On(bot, "chat")
            def chat(this, username, message, *args):
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
                    bot.chat('24 ATERNOS > Bot stopped! - Made By Fortcote')
                    bot.clearControlStates()

            @On(bot, "spawn")
            def spawn(this):
                bot.chat("Bot > Spawned!")

            @On(bot, "death")
            def death(this):
                bot.chat("Bot > Respawn!")

            break  # اتصال موفق بود، از loop خارج شو

        except Exception as e:
            print(f"[Retrying in 30s] Connection failed: {e}")
            time.sleep(30)  # صبر کن و دوباره تلاش کن

def run_flask():
    app.run(host="0.0.0.0", port=8080)

if __name__ == '__main__':
    _thread.start_new_thread(start_bot, ())  # اجرای بات در thread جدا
    run_flask()  # اجرای Flask
