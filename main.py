from currency import get_balance, add_balance, subtract_balance, get_all_balances
from equipment import get_equipment
from discord import app_commands  # スラッシュコマンド用
from keep_alive import keep_alive
keep_alive()

import discord
from discord.ext import commands
import os

# インテント設定
intents = discord.Intents.default()
intents.message_content = True

# Botとスラッシュコマンドの準備
bot = commands.Bot(command_prefix="!", intents=intents)
tree = app_commands.CommandTree(bot)

# Bot起動時
@bot.event
async def on_ready():
    await tree.sync()  # スラッシュコマンドを同期
    print(f"✅ ログイン成功: {bot.user}")

# スラッシュコマンド：残高確認（自分だけに表示）
@tree.command(name="残高確認", description="自分の残高を確認します")
async def check_balance(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    balance = get_balance(user_id)
    await interaction.response.send_message(
        f"{interaction.user.mention} の starcoin 残高：{balance} SC",
        ephemeral=True  # 自分だけ見えるメッセージ
    )

# 通常コマンド例：ping
@bot.command()
async def ping(ctx):
    await ctx.send("ぽん！")

# Bot起動
bot.run(os.environ["TOKEN"])
