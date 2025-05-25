from configparser import ConfigParser
from javascript import require, On
from flask import Flask
import threading, os
from sys import platform

# Load mineflayer
mineflayer = require('mineflayer')

# Load config.ini
config = ConfigParser()
config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
print(f"Reading config from: {config_path}")
config.read(config_path)
print("Config sections:", config.sections())

# Flask app
app = Flask(__name__)

@app.route("/", methods=["GET", "HEAD"])
def home():
    return "Bot is running", 200

# Bot logic
def started(stop):
    bot = mineflayer.createBot({
        'host': config.get('server', 'host'),
        'port': int(config.get('server', 'port')),
        'username': config.get('bot', 'name')
    })
    print('Bot started')

    @On(bot, "login")
    def login(this):
        bot.chat(config.get('bot', 'register'))
        bot.chat(config.get('bot', 'login'))
        print("Bot online")

    @On(bot, "error")
    def error(err, *a):
        print("Connect ERROR:", err, a)

    @On(bot, "kicked")
    def kicked(this, reason, *a):
        print("I was kicked:", reason, a)
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
            bot.chat('24 ATERNOS > Bot stopped! - Made By Fortcote')
            bot.clearControlStates()

    @On(bot, "spawn")
    def spawn(this):
        bot.chat("Bot > Spawned!")

    @On(bot, "death")
    def death(this):
        bot.chat("Bot > Respawn!")

# Start bot thread
def start_bot():
    thread = threading.Thread(target=started, args=(lambda: False,))
    thread.start()

# Flask + Bot start
if __name__ == '__main__':
    start_bot()
    port = int(os.environ.get("PORT", 8080))  # Render uses $PORT
    app.run(host='0.0.0.0', port=port)
