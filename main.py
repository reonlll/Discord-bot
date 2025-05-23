# --- 必要なインポート ---
import os
import discord
from discord.ext import commands
from discord import app_commands
from currency import get_balance, add_balance, subtract_balance, get_all_balances
from equipment import get_equipment

# --- Intents の設定 ---
intents = discord.Intents.default()
intents.message_content = True

# --- Bot と CommandTree の初期化 ---
bot = commands.Bot(command_prefix="!", intents=intents)
tree = app_commands.CommandTree(bot)

# --- Bot起動時にスラッシュコマンドを同期 ---
@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ ログイン成功: {bot.user}")

# --- スラッシュコマンド: /残高確認 ---
@tree.command(name="残高確認", description="自分のstarcoin残高を確認します")
async def check_balance(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    balance = get_balance(user_id)
    await interaction.response.send_message(
        f"{interaction.user.mention} の starcoin 残高: {balance} SC",
        ephemeral=True  # 自分にだけ表示
    )

# --- 通常コマンド: !ping ---
@bot.command()
async def ping(ctx):
    await ctx.send("ぽん！")

# --- 通常コマンド: !equipment（装備確認）---
@bot.command()
async def equipment(ctx):
    eq = get_equipment(ctx.author.id)
    await ctx.send(
        f"**{ctx.author.name} の装備：**\n"
        f"武器：{eq['weapon'] or 'なし'}\n"
        f"防具：{eq['armor'] or 'なし'}\n"
        f"アイテム：{eq['item'] or 'なし'}"
    )

# --- Botトークンで起動 ---
bot.run(os.environ["TOKEN"])
