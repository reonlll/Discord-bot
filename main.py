from currency import get_balance, add_balance, subtract_balance, get_all_balances
from equipment import get_equipment
from discord import app_commands  # スラッシュコマンド用

from keep_alive import keep_alive
keep_alive()

import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = app_commands.CommandTree(bot)

@bot.event
async def on_ready():
    await tree.sync()  # ←これを追加！
    print(f"✅ ログイン成功: {bot.user}")

@tree.command(name="残高確認", description="自分のstarcoin残高を表示します")
async def check_balance(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    balance = get_balance(user_id)
    await interaction.response.send_message(
        f"{interaction.user.mention} のstarcoin残高：{balance} SC", ephemeral=True
    )

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
