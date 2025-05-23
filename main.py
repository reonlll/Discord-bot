from currency import get_balance, add_balance, subtract_balance, get_all_balances
from equipment import get_equipment
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

# 残高確認（自分だけ）
@bot.command()
async def coin(ctx):
    user_id = str(ctx.author.id)
    balance = get_balance(user_id)
    await ctx.author.send(f"{ctx.author.mention} の starcoin 残高：{balance} SC")  # DMで送信

# starcoin 付与（管理者限定）
@bot.command()
@commands.has_permissions(administrator=True)
async def give(ctx, member: discord.Member, amount: int):
    user_id = str(member.id)
    add_balance(user_id, amount)
    await ctx.send(f"{member.mention} に {amount} SC を付与しました。")

# starcoin 送金
@bot.command()
async def send(ctx, member: discord.Member, amount: int):
    sender_id = str(ctx.author.id)
    receiver_id = str(member.id)
    if subtract_balance(sender_id, amount):
        add_balance(receiver_id, amount)
        await ctx.send(f"{ctx.author.mention} から {member.mention} に {amount} SC を送金しました。")
    else:
        await ctx.send("残高が足りません。")

# pingテスト
@bot.command()
async def ping(ctx):
    await ctx.send("ぽん！")

# 装備確認
@bot.command()
async def equipment(ctx):
    eq = get_equipment(ctx.author.id)
    await ctx.send(
        f"**{ctx.author.name} の装備：**\n"
        f"武器：{eq['weapon'] or 'なし'}\n"
        f"防具：{eq['armor'] or 'なし'}\n"
        f"アイテム：{eq['item'] or 'なし'}"
    )

bot.run(os.environ["TOKEN"])
