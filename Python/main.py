from configparser import ConfigParser
from javascript import require, On
from flask import Flask
import threading, os, random, time
from sys import platform

mineflayer = require('mineflayer')
Vec3 = require('vec3')

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running"

def run_flask():
    app.run(host="0.0.0.0", port=10000)

threading.Thread(target=run_flask).start()

config = ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))

def started(stop):
    bot = mineflayer.createBot({
        'host': config.get('server', 'host'),
        'port': int(config.get('server', 'port')),
        'username': config.get('bot', 'name')
    })

    @On(bot, 'login')
    def login(this):
        bot.chat(config.get('bot', 'register'))
        bot.chat(config.get('bot', 'login'))
        print("Bot online")

    @On(bot, 'spawn')
    def spawn(this):
        bot.chat("Spawned and ready!")
        random_move()

    @On(bot, 'chat')
    def chat(this, username, message, *args):
        if username == bot.username:
            return

        def get_cmd(key):
            return config.get('command', key)

        if message.startswith(get_cmd('position')):
            p = bot.entity.position
            bot.chat(f"I'm at {p}")

        elif message.startswith(get_cmd('start')):
            bot.chat("Starting movement")
            random_move()

        elif message.startswith(get_cmd('stop')):
            bot.clearControlStates()
            bot.chat("Stopped moving")

        elif message.startswith(get_cmd('follow')):
            name = message.split(' ')[1]
            target = bot.players.get(name)
            if target and target.entity:
                bot.chat(f"Following {name}")
                bot.pathfinder.setGoal(mineflayer.pathfinder.goals.GoalFollow(target.entity, 1))

        elif message.startswith(get_cmd('collect')):
            try:
                _, item, count = message.split()
                count = int(count)
                bot.chat(f"Collecting {count} {item}")
                collect_item(item, count)
            except:
                bot.chat("Usage: ;collect <item> <count>")

        elif message.startswith(get_cmd('drop')):
            try:
                _, item, count = message.split()
                count = int(count)
                drop_item(item, count)
            except:
                bot.chat("Usage: ;drop <item> <count>")

        elif message.startswith(get_cmd('biome')):
            name = message.split(' ')[1].lower()
            bot.chat(f"Looking for biome {name}")
            # نیاز به پلاگین یا اسکن بایوم‌ها دارد (برای توسعه کامل)

        elif message.startswith(get_cmd('plant')):
            plant_seed()

        elif message.startswith(get_cmd('bridge')):
            build_bridge()

        elif message.startswith(get_cmd('hunt')):
            hunt_animals()

        elif message.startswith(get_cmd('armor')):
            equip_armor()

        elif message.startswith(get_cmd('eat')):
            eat_food()

    def random_move():
        def loop():
            while True:
                time.sleep(random.randint(10, 20))
                if random.choice([True, False]):
                    bot.setControlState('forward', True)
                    bot.setControlState('jump', True)
                    time.sleep(2)
                    bot.clearControlStates()
        threading.Thread(target=loop).start()

    def collect_item(name, target_count):
        count = 0
        def cb(block):
            return block.name == name
        blocks = bot.findBlocks({'matching': cb, 'maxDistance': 64, 'count': 100})
        for pos in blocks:
            if count >= target_count:
                break
            bot.dig(bot.blockAt(pos))
            count += 1
        bot.chat(f"Collected {count} {name}")

    def drop_item(name, count):
        for item in bot.inventory.items():
            if item.name == name:
                bot.toss(item.type, None, min(count, item.count))
                bot.chat(f"Dropped {min(count, item.count)} {name}")
                break

    def plant_seed():
        for slot in bot.inventory.items():
            if 'seeds' in slot.name:
                bot.equip(slot, 'hand')
                for dx in range(-5, 5):
                    for dz in range(-5, 5):
                        pos = bot.entity.position.offset(dx, -1, dz)
                        block = bot.blockAt(pos)
                        if block and block.name == 'farmland':
                            bot.placeBlock(block, Vec3(0, 1, 0))
                            bot.chat("Seed planted")
                            return

    def build_bridge():
        forward = bot.entity.position.offset(0, -1, 1)
        block = bot.blockAt(forward)
        if block and block.name == 'air':
            for item in bot.inventory.items():
                if 'planks' in item.name:
                    bot.equip(item, 'hand')
                    bot.placeBlock(bot.blockAt(bot.entity.position.offset(0, -1, 0)), Vec3(0, 1, 0))
                    bot.chat("Bridge placed")
                    return

    def hunt_animals():
        targets = [e for e in bot.entities.values() if e.name in ['cow', 'sheep', 'pig', 'chicken']]
        for target in targets:
            bot.attack(target)
            bot.chat(f"Attacked {target.name}")

    def equip_armor():
        for item in bot.inventory.items():
            if 'helmet' in item.name or 'chestplate' in item.name or 'leggings' in item.name or 'boots' in item.name:
                bot.equip(item, 'torso')
                bot.chat("Armor equipped")

    def eat_food():
        for item in bot.inventory.items():
            if 'cooked' in item.name or 'beef' in item.name or 'porkchop' in item.name:
                bot.equip(item, 'hand')
                bot.consume()
                bot.chat("Ate food")
                return

    @On(bot, 'death')
    def died(this):
        bot.chat("I died! Respawning...")

    @On(bot, 'kicked')
    def kicked(this, reason):
        print("Kicked:", reason)
        bot.chat("Disconnected")

    @On(bot, 'error')
    def error(err):
        print("Error:", err)


def start():
    global bot_thread
    bot_thread = threading.Thread(target=started, args=(lambda: False,))
    bot_thread.start()

def stop():
    try:
        if platform == "win32":
            os.system('taskkill /f /im node.exe')
        else:
            os.system('killall node')
    except:
        pass

if __name__ == '__main__':
    start()
