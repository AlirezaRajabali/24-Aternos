from flask import Flask
import os, threading, random, time
from sys import platform
from configparser import ConfigParser
from javascript import require, On

mineflayer = require('mineflayer')
autoeat = require('mineflayer-auto-eat')
pathfinder = require('mineflayer-pathfinder').pathfinder
{ GoalNear, GoalBlock } = require('mineflayer-pathfinder').goals
collectBlock = require('mineflayer-collectblock').plugin
pvp = require('mineflayer-pvp').plugin
armorManager = require('mineflayer-armor-manager')
mcData = require('minecraft-data')

config = ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running"

def run_flask():
    app.run(host="0.0.0.0", port=10000)
threading.Thread(target=run_flask).start()

def start_bot():
    bot = mineflayer.createBot({
        'host': config.get('server', 'host'),
        'port': int(config.get('server', 'port')),
        'username': config.get('bot', 'name')
    })

    bot.loadPlugin(pathfinder)
    bot.loadPlugin(collectBlock)
    bot.loadPlugin(autoeat)
    bot.loadPlugin(pvp)
    bot.loadPlugin(armorManager)

    bot.once('spawn', lambda: bot.chat("Bot > Spawned!"))

    @On(bot, 'login')
    def handle_login(this):
        bot.chat(config.get('bot', 'register'))
        bot.chat(config.get('bot', 'login'))

    @On(bot, 'chat')
    def chat(this, username, message, *_):
        if username == bot.username:
            return

        args = message.split()
        cmd = args[0]

        if cmd == config.get('command', 'position'):
            bot.chat(f"Bot > I'm at {bot.entity.position}")

        elif cmd == config.get('command', 'start'):
            bot.setControlState('forward', True)
            bot.setControlState('jump', True)
            bot.setControlState('sprint', True)
            bot.chat("Bot started!")

        elif cmd == config.get('command', 'stop'):
            bot.clearControlStates()
            bot.chat("Bot stopped!")

        elif cmd == ';follow' and len(args) > 1:
            target = bot.players[args[1]]
            if target and target.entity:
                bot.pathfinder.setGoal(GoalNear(target.entity.position.x, target.entity.position.y, target.entity.position.z, 1))
                bot.chat(f"Following {args[1]}")

        elif cmd == ';collect' and len(args) > 2:
            item, count = args[1], int(args[2])
            blocks = bot.findBlocks({
                'matching': mcData(bot.version).itemsByName[item].id,
                'maxDistance': 64,
                'count': count
            })
            if blocks:
                bot.chat(f"Collecting {count} {item}")
                bot.collectBlock.collect(blocks[:count], lambda err: bot.chat(f"Done collecting {item}" if not err else f"Error: {err}"))

        elif cmd == ';drop' and len(args) > 2:
            item, count = args[1], int(args[2])
            for i in bot.inventory.items():
                if i.name == item:
                    dropCount = min(i.count, count)
                    bot.toss(i.type, None, dropCount, lambda err: bot.chat(f"Dropped {dropCount} {item}" if not err else f"Drop error: {err}"))
                    break

        elif cmd == ';killmobs':
            mobs = [e for e in bot.entities.values() if e.kind == 'Hostile mobs']
            if mobs:
                bot.pvp.attack(mobs[0])
                bot.chat("Attacking mob!")

        elif cmd == ';hunt':
            animals = [e for e in bot.entities.values() if e.name in ['cow', 'sheep', 'pig', 'chicken']]
            if animals:
                bot.pvp.attack(animals[0])
                bot.chat(f"Hunting {animals[0].name}!")

        elif cmd == ';biome' and len(args) > 1:
            target_biome = args[1].lower()
            bot.chat(f"Searching for biome {target_biome} (placeholder only)")
            # Real biome navigation requires mapping and scanning, placeholder for now

        elif cmd == ';plant':
            seeds = [i for i in bot.inventory.items() if 'seeds' in i.name]
            if seeds:
                bot.chat("Planting seeds")
                # Simplified: actual planting logic needs block checking, etc

        elif cmd == ';bridge':
            bot.chat("Building a bridge forward (placeholder only)")
            # Full bridge building logic needs location tracking and block placement

        elif cmd == ';armor':
            bot.chat("Equipping best armor")
            bot.armorManager.equipAll()

        elif cmd == ';eat':
            bot.chat("Trying to eat food")
            bot.autoEat.enable()

    def random_movement():
        while True:
            if bot.entity:
                bot.setControlState('forward', bool(random.getrandbits(1)))
                bot.setControlState('jump', bool(random.getrandbits(1)))
            time.sleep(10)

    threading.Thread(target=random_movement).start()

if __name__ == '__main__':
    threading.Thread(target=start_bot).start()
