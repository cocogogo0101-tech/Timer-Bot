import discord
from discord.ext import commands
import time
import threading
from flask import Flask

# --------- KEEP ALIVE ---------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive"

def run_web():
    app.run(host="0.0.0.0", port=3000)

threading.Thread(target=run_web).start()

# --------- DISCORD BOT ---------
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command()
async def timer(ctx, minutes: int):
    end_time = time.time() + (minutes * 60)
    msg = await ctx.send(f"⏳ الوقت المتبقي: {minutes} دقيقة")

    while True:
        remaining = int(end_time - time.time())

        if remaining <= 0:
            await msg.edit(content=f"⏰ انتهى الوقت! {ctx.author.mention}")
            break

        mins = remaining // 60 + 1
        await msg.edit(content=f"⏳ الوقت المتبقي: {mins} دقيقة")
        await discord.utils.sleep_until(
            discord.utils.utcnow().fromtimestamp(time.time() + 30)
        )

bot.run(os.environ["TOKEN"])