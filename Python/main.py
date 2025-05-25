from configparser import ConfigParser
from javascript import require, On
import threading, os, random, time
from sys import platform
from flask import Flask

mineflayer = require('mineflayer')
autoeat = require('mineflayer-auto-eat')
pathfinder = require('mineflayer-pathfinder').pathfinder
mcData = require('minecraft-data')
collectBlock = require('mineflayer-collectblock').plugin
pvp = require('mineflayer-pvp').plugin
armorManager = require('mineflayer-armor-manager')

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is running"

# استفاده از PORT محیطی که Render فراهم می‌کند
port = int(os.environ.get("PORT", 10000))
threading.Thread(target=lambda: app.run(host="0.0.0.0", port=port), daemon=True).start()

config = ConfigParser()
config.read('config.ini')

actions = {}

def stop_actions():
    for action in actions.values():
        if callable(action):
            action()
    actions.clear()

def create_and_start_bot():
    try:
        bot = mineflayer.createBot({
            'host': config.get('server', 'host'),
            'port': int(config.get('server', 'port')),
            'username': config.get('bot', 'name')
        })
    except Exception as e:
        print(f"Error creating bot: {e}")
        time.sleep(5)
        return create_and_start_bot()

    bot.loadPlugin(pathfinder)
    bot.loadPlugin(collectBlock)
    bot.loadPlugin(pvp)
    bot.loadPlugin(autoeat)
    bot.loadPlugin(armorManager)

    bot.once('spawn', lambda: bot.chat("Bot > Spawned!"))

    @On(bot, 'login')
    def on_login(this):
        time.sleep(1)
        bot.chat(config.get('bot', 'register'))
        time.sleep(1)
        bot.chat(config.get('bot', 'login'))

    @On(bot, 'chat')
    def on_chat(this, username, message, *args):
        if username == bot.username:
            return
        
        msg = message.strip().lower()

        if msg == config.get('command', 'stop'):
            stop_actions()
            bot.clearControlStates()
            bot.chat('Bot > All actions stopped.')

        elif msg == ';sleep':
            bed = bot.findBlock({'matching': bot.registry.blocksByName.bed.id, 'maxDistance': 16})
            if bed:
                bot.chat("Bot > Trying to sleep... 🛏️")
                bot.sleep(bed, lambda err=None: bot.chat("Bot > Sleeping..." if not err else f"Bot > Can't sleep: {err}"))
            else:
                bot.chat("Bot > No bed nearby.")

        elif msg == ';wake':
            if bot.isSleeping():
                bot.wake(lambda: bot.chat("Bot > Woke up."))
            else:
                bot.chat("Bot > I'm not sleeping.")

    @On(bot, 'death')
    def on_death(this):
        bot.chat("Bot > I died!")

    @On(bot, 'end')
    def on_end(this):
        print("Bot disconnected. Reconnecting in 5 seconds...")
        time.sleep(5)
        create_and_start_bot()

    @On(bot, 'error')
    def on_error(this, err):
        print(f"❌ Bot Error: {err}")

    @On(bot, 'kicked')
    def on_kicked(this, reason, loggedIn):
        print(f"🚫 Kicked from server: {reason}")

    def random_movement():
        directions = ['forward', 'back', 'left', 'right']
        while actions.get('random_walk'):
            dir = random.choice(directions)
            bot.setControlState(dir, True)
            time.sleep(random.uniform(1, 2))
            bot.setControlState(dir, False)
            time.sleep(random.uniform(2, 4))

    def auto_walk():
        actions['random_walk'] = True
        threading.Thread(target=random_movement).start()

    def auto_eat():
        bot.autoEat.options = {
            'priority': 'foodPoints',
            'startAt': 14,
            'banFoods': []
        }
        bot.autoEat.enable()

    def auto_attack():
        def loop():
            while actions.get('attack'):
                entity = bot.nearestEntity(lambda e: e.type == 'mob' and e.mobType != 'ArmorStand')
                if entity:
                    bot.pvp.attack(entity)
                time.sleep(1)
        actions['attack'] = True
        threading.Thread(target=loop).start()

    auto_walk()
    auto_eat()
    auto_attack()

# اجرای اولیه
threading.Thread(target=create_and_start_bot).start()
