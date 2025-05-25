# main.py
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

def run_flask():
    app.run(host="0.0.0.0", port=10000)
threading.Thread(target=run_flask).start()

config = ConfigParser()
config.read('config.ini')

actions = {}

def stop_actions():
    for action in actions.values():
        if callable(action):
            action()
    actions.clear()

def start_bot():
    bot = mineflayer.createBot({
        'host': config.get('server', 'host'),
        'port': int(config.get('server', 'port')),
        'username': config.get('bot', 'name')
    })

    bot.loadPlugin(pathfinder)
    bot.loadPlugin(collectBlock)
    bot.loadPlugin(pvp)
    bot.loadPlugin(autoeat)
    bot.loadPlugin(armorManager)

    bot.once('spawn', lambda: bot.chat("Bot > Spawned!"))

    @On(bot, 'login')
    def on_login(this):
        bot.chat(config.get('bot', 'register'))
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
            bed = bot.findBlock({
                'matching': bot.registry.blocksByName.bed.id,
                'maxDistance': 16
            })
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

    def random_movement():
        directions = ['forward', 'back', 'left', 'right']
        while True:
            if not bot.entity:
                continue
            if not actions.get('random_walk'):
                break
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
            while True:
                if not actions.get('attack'):
                    break
                entity = bot.nearestEntity(lambda e: e.type == 'mob' and e.mobType != 'ArmorStand')
                if entity:
                    bot.pvp.attack(entity)
                time.sleep(1)
        actions['attack'] = True
        threading.Thread(target=loop).start()

    auto_walk()
    auto_eat()
    auto_attack()

threading.Thread(target=start_bot).start()
