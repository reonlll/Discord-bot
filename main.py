import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ ログイン成功: {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("ぽん！")

bot.run(os.environ["TOKEN"])
