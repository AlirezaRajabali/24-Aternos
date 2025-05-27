from configparser import ConfigParser
from javascript import require, On
from flask import Flask
import threading, os, random, time
from sys import platform

mineflayer = require('mineflayer')
Vec3 = require('vec3')
app = Flask(__name__)

config = ConfigParser()
config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
config.read(config_path)

bot = None
reconnect_attempts = 0
max_reconnect_attempts = 5

def try_reconnect():
    global reconnect_attempts
    if reconnect_attempts < max_reconnect_attempts:
        reconnect_attempts += 1
        print(f"🔁 تلاش برای ری‌کانکت ({reconnect_attempts}/{max_reconnect_attempts}) در ۵ ثانیه...")
        time.sleep(5)
        started(lambda: False)
    else:
        print("❌ تلاش‌های ری‌کانکت تموم شد. بات متوقف شد.")

def afk_bypass_loop():
    directions = ['forward', 'back', 'left', 'right']
    while True:
        time.sleep(5)
        if not bot or not bot.entity or not bot.entity.position:
            continue

        action = random.choice(['move', 'jump', 'sneak', 'chat', 'stop'])
        if action == 'jump':
            bot.setControlState('jump', True)
            time.sleep(0.5)
            bot.setControlState('jump', False)

        elif action == 'sneak':
            bot.setControlState('sneak', True)
            time.sleep(2)
            bot.setControlState('sneak', False)

        elif action == 'chat':
            msg = random.choice([
                "🤖 من یک بازیکنم!",
                "هی! اینجا چه خبره؟",
                "🟢 آنلاین هستم هنوز!",
                "بازم AFK فکر کردی؟ نه عزیزم"
            ])
            bot.chat(msg)

        elif action == 'move':
            dir = random.choice(directions)
            bot.setControlState(dir, True)
            time.sleep(random.uniform(1, 2))
            bot.setControlState(dir, False)

        elif action == 'stop':
            bot.clearControlStates()

def started(stop):
    global bot, reconnect_attempts
    reconnect_attempts = 0

    bot = mineflayer.createBot({
        'host': config.get('server', 'host'),
        'port': int(config.get('server', 'port')),
        'username': config.get('bot', 'name')
    })

    @On(bot, "login")
    def login(this):
        bot.chat(config.get('bot', 'register'))
        bot.chat(config.get('bot', 'login'))
        print("✅ وارد حساب شد")

    @On(bot, "spawn")
    def spawn(this):
        bot.chat("✅ وارد بازی شدم!")
        threading.Thread(target=afk_bypass_loop, daemon=True).start()

    @On(bot, "chat")
    def handle(this, username, message, *args):
        if username == bot.username:
            return
        if message.startswith(config.get('command', 'position')):
            p = bot.entity.position
            bot.chat(f"I'm at {p.toString()}")
        elif message.startswith(config.get('command', 'start')):
            bot.chat("▶️ در حال حرکت...")
            bot.setControlState('forward', True)
            bot.setControlState('jump', True)
            bot.setControlState('sprint', True)
        elif message.startswith(config.get('command', 'stop')):
            bot.chat("⏹️ توقف!")
            bot.clearControlStates()
        elif message.startswith(";follow "):
            name = message.split(" ", 1)[1]
            target = bot.players.get(name)
            if target and target.entity:
                bot.chat(f"🔁 دنبال کردن {name}")
                bot.lookAt(target.entity.position.offset(0, 1.6, 0))
                bot.setControlState('forward', True)
            else:
                bot.chat("❌ پلیر پیدا نشد.")
        elif message.startswith(";eat"):
            food = None
            for item in bot.inventory.items():
                if 'bread' in item.name or 'apple' in item.name:
                    food = item
                    break
            if food:
                bot.equip(food, 'hand', lambda: bot.activateItem())
                bot.chat("🍎 در حال خوردن غذا...")
        elif message.startswith(";fight"):
            nearest = bot.nearestEntity(lambda e: e.kind == 'Hostile mobs')
            if nearest:
                bot.chat("⚔️ حمله به ماب نزدیک...")
                bot.attack(nearest)
            else:
                bot.chat("❌ مابی نزدیک نیست.")

    @On(bot, "error")
    def error(this, err, *a):
        print("❌ خطا:", err)
        bot.end()
        try_reconnect()

    @On(bot, "kicked")
    def kicked(this, reason, *a):
        print("⛔ کیک شد:", reason)
        bot.end()
        try_reconnect()

@app.route('/')
def home():
    return "🤖 Bot is running", 200

def start_bot():
    t = threading.Thread(target=started, args=(lambda: False,), daemon=True)
    t.start()

if __name__ == '__main__':
    start_bot()
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

