from configparser import ConfigParser
from javascript import require, On
from flask import Flask
import threading, os
from sys import platform

mineflayer = require('mineflayer')
app = Flask(__name__)

config = ConfigParser()
config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
print(f"Reading config from: {config_path}")
config.read(config_path)
print("Config sections:", config.sections())

bot = None

def started(stop):
    global bot
    bot = mineflayer.createBot({
        'host': config.get('server', 'host'),
        'port': int(config.get('server', 'port')),
        'username': config.get('bot', 'name')
    })
    print('Bot started.')

    @On(bot, "login")
    def login(this):
        bot.chat(config.get('bot', 'register'))
        bot.chat(config.get('bot', 'login'))
        print("Bot logged in")

    @On(bot, "spawn")
    def spawn(this):
        bot.chat("Spawned!")

    @On(bot, "chat")
    def handle(this, username, message, *args):
        if username == bot.username:
            return
        if message.startswith(config.get('command', 'position')):
            p = bot.entity.position
            bot.chat(f"I'm at {p.toString()}")
        elif message.startswith(config.get('command', 'start')):
            bot.chat("Starting...")
            bot.setControlState('forward', True)
            bot.setControlState('jump', True)
            bot.setControlState('sprint', True)
        elif message.startswith(config.get('command', 'stop')):
            bot.chat("Stopping...")
            bot.clearControlStates()

    @On(bot, "error")
    def error(this, err, *a):
        print("Bot error:", err)

    @On(bot, "kicked")
    def kicked(this, reason, *a):
        print("Kicked:", reason)
        bot.end()

@app.route('/')
def home():
    return "✅ Bot is running", 200

def start_bot():
    t = threading.Thread(target=started, args=(lambda: False,))
    t.start()

if __name__ == '__main__':
    start_bot()
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
