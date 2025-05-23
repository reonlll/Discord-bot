from currency import get_balance, add_balance, subtract_balance

from keep_alive import keep_alive
keep_alive()

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
async def balance(ctx):
    user_id = str(ctx.author.id)
    balance = get_balance(user_id)
    await ctx.send(f"{ctx.author.mention} のスターコイン残高：{balance} SC")

@bot.command()
@commands.has_permissions(administrator=True)
async def give(ctx, member: discord.Member, amount: int):
    user_id = str(member.id)
    add_balance(user_id, amount)
    await ctx.send(f"{member.mention} に {amount} SC を付与しました。")

@bot.command()
async def send(ctx, member: discord.Member, amount: int):
    sender_id = str(ctx.author.id)
    receiver_id = str(member.id)
    if subtract_balance(sender_id, amount):
        add_balance(receiver_id, amount)
        await ctx.send(f"{ctx.author.mention} から {member.mention} に {amount} SC を送金しました。")
    else:
        await ctx.send("残高が足りません。")
@bot.command()
async def ping(ctx):
    await ctx.send("ぽん！")

bot.run(os.environ["TOKEN"])
