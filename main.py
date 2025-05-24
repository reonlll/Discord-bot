import discord
from discord.ext import commands
from discord import app_commands
import os

from currency import get_balance, add_balance, subtract_balance, get_all_balances
from equipment import get_equipment, set_equipment
from keep_alive import keep_alive
keep_alive()

# Intents（メッセージ内容取得を有効に）
intents = discord.Intents.default()
intents.message_content = True

# BotとCommandTree初期化
bot = commands.Bot(command_prefix="!", intents=intents)

# Bot起動時：スラッシュコマンドを同期
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ ログイン成功: {bot.user}")

# --- スラッシュコマンド ---

@bot.tree.command(name="ギルドカード", description="自分のスターコイン残高と装備を表示します")
async def guild_card(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    balance = get_balance(user_id)
    eq = get_equipment(interaction.user.id)

    message = (
        f"**{interaction.user.name} のギルドカード**\n"
        f"スターコイン：{balance} SC\n\n"
        f"【装備】\n"
        f"武器：{eq['weapon'] or 'なし'}\n"
        f"防具：{eq['armor'] or 'なし'}\n"
        f"アイテム：{eq['item'] or 'なし'}"
    )

    await interaction.response.send_message(message, ephemeral=True)

import json
import os
from discord import app_commands
import discord

EQUIP_FILE = "equipment.json"

def save_equipment(user_id, weapon=None, armor=None):
    if os.path.exists(EQUIP_FILE):
        with open(EQUIP_FILE, "r") as f:
            data = json.load(f)
    else:
        data = {}

    if str(user_id) not in data:
        data[str(user_id)] = {}

    if weapon:
        data[str(user_id)]["weapon"] = weapon
    if armor:
        data[str(user_id)]["armor"] = armor

    with open(EQUIP_FILE, "w") as f:
        json.dump(data, f, indent=4)

@bot.tree.command(name="装備", description="武器または防具を装備します")
@app_commands.describe(
    weapon="装備する武器（例: 木の剣, 鉄の剣, 炎の剣）",
    armor="装備する防具（例: 布の服, 鉄の鎧, ドラゴンアーマー）"
)
async def equip(interaction: discord.Interaction, weapon: str = None, armor: str = None):
    if weapon is None and armor is None:
        await interaction.response.send_message("武器または防具のどちらかを指定してください。", ephemeral=True)
        return

    save_equipment(interaction.user.id, weapon, armor)
    response = f"{interaction.user.mention} の装備を更新しました：\n"
    if weapon:
        response += f"- 武器：{weapon}\n"
    if armor:
        response += f"- 防具：{armor}\n"

    await interaction.response.send_message(response, ephemeral=True)

import json
import os
from discord import app_commands
import discord

EQUIP_FILE = "equipment.json"

def load_equipment(user_id):
    if os.path.exists(EQUIP_FILE):
        with open(EQUIP_FILE, "r") as f:
            data = json.load(f)
        return data.get(str(user_id), {})
    return {}

@bot.tree.command(name="装備一覧", description="現在の装備を確認します")
async def show_equipment(interaction: discord.Interaction):
    equip = load_equipment(interaction.user.id)
    weapon = equip.get("weapon", "未装備")
    armor = equip.get("armor", "未装備")
    item = equip.get("item", "未装備")

    msg = (
        f"**{interaction.user.name} の現在の装備**\n"
        f"武器：{weapon}\n"
        f"防具：{armor}\n"
        f"アイテム：{item}"
    )
    await interaction.response.send_message(msg, ephemeral=True)

# 残高確認
@bot.tree.command(name="残高確認", description="自分のstarcoin残高を確認します")
async def check_balance(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    balance = get_balance(user_id)
    await interaction.response.send_message(
        f"{interaction.user.mention} の starcoin 残高：{balance} SC",
        ephemeral=True  # 自分にだけ表示
    )

@bot.tree.command(name="送金", description="他のユーザーにスターコインを送ります")
@app_commands.describe(user="送金先のユーザー", amount="送るコインの枚数")
async def send(interaction: discord.Interaction, user: discord.Member, amount: int):
    sender_id = str(interaction.user.id)
    receiver_id = str(user.id)

    if sender_id == receiver_id:
        await interaction.response.send_message("自分自身には送金できません。", ephemeral=True)
        return

    if amount <= 0:
        await interaction.response.send_message("1以上の金額を指定してください。", ephemeral=True)
        return

    sender_balance = get_balance(sender_id)
    if sender_balance < amount:
        await interaction.response.send_message("残高が不足しています。", ephemeral=True)
        return

    subtract_balance(sender_id, amount)
    add_balance(receiver_id, amount)

    await interaction.response.send_message(
        f"{user.mention} に {amount} starcoin を送りました！"
    )

    # 残高ファイル読み込み
    try:
        with open("coin.json", "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}

    # 初期化
    if sender_id not in data:
        data[sender_id] = {"coin": 0}
    if receiver_id not in data:
        data[receiver_id] = {"coin": 0}

    # 残高チェック
    if data[sender_id]["coin"] < amount:
        await interaction.response.send_message("スターコインが足りません。", ephemeral=True)
        return

    # 送金処理
    data[sender_id]["coin"] -= amount
    data[receiver_id]["coin"] += amount

    # 保存
    with open("coin.json", "w") as f:
        json.dump(data, f, indent=4)

    await interaction.response.send_message(
        f"{user.mention} に {amount} starcoin を送りました！",
        ephemeral=True
    )

from discord import app_commands
from discord.ext import commands

@bot.tree.command(name="コイン付与", description="指定したユーザーにスターコインを付与します")
@app_commands.describe(user="付与する相手", amount="付与するスターコインの額")
@app_commands.checks.has_permissions(administrator=True)
async def coin_grant(interaction: discord.Interaction, user: discord.Member, amount: int):
    if amount <= 0:
        await interaction.response.send_message("1以上の金額を指定してください。", ephemeral=True)
        return

    add_balance(str(user.id), amount)
    await interaction.response.send_message(
        f"{user.mention} に {amount} starcoin を付与しました！", ephemeral=True
    )

# アイテム装備
@bot.tree.command(name="アイテム装備", description="指定したアイテムを装備します")
@app_commands.describe(name="装備するアイテム名")
async def item_set(interaction: discord.Interaction, name: str):
    user_id = str(interaction.user.id)
    set_equipment(user_id, "item", name)
    await interaction.response.send_message(f"アイテム「{name}」を装備しました！", ephemeral=True)


# アイテム外す
@bot.tree.command(name="アイテム外す", description="現在のアイテム装備を外します")
async def item_remove(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    set_equipment(user_id, "item", None)
    await interaction.response.send_message("アイテムを外しました。", ephemeral=True)

# 装備確認
@bot.tree.command(name="装備確認", description="自分の現在の装備を表示します")
async def show_equipment(interaction: discord.Interaction):
    eq = get_equipment(interaction.user.id)
    await interaction.response.send_message(
        f"**{interaction.user.name} の装備：**\n"
        f"武器：{eq['weapon'] or 'なし'}\n"
        f"防具：{eq['armor'] or 'なし'}\n"
        f"アイテム：{eq['item'] or 'なし'}",
        ephemeral=True
    )

@bot.tree.command(name="pvp", description="対戦相手とPvPバトルをします")
@app_commands.describe(opponent="対戦相手")
async def pvp(interaction: discord.Interaction, opponent: discord.Member):
    if opponent.id == interaction.user.id:
        await interaction.response.send_message("自分自身とは対戦できません。", ephemeral=True)
        return

    # 装備取得
    atk_eq = get_equipment(interaction.user.id)
    def_eq = get_equipment(opponent.id)

    atk_power = weapon_power(atk_eq["weapon"])
    atk_def = armor_defense(atk_eq["armor"])
    def_power = weapon_power(def_eq["weapon"])
    def_def = armor_defense(def_eq["armor"])

    # HP初期化
    atk_hp = 100
    def_hp = 100

    # 攻撃者の攻撃
    atk_dice = random.randint(1, 3)
    def_dice = random.randint(1, 3)
    damage_to_def = max(1, atk_power * atk_dice - def_def * def_dice)
    def_hp -= damage_to_def

    # 反撃
    def_atk_dice = random.randint(1, 3)
    atk_def_dice = random.randint(1, 3)
    damage_to_atk = max(1, def_power * def_atk_dice - atk_def * atk_def_dice)
    atk_hp -= damage_to_atk

    # バトルログ生成
    log = f"**【PvPバトル】**\n"
    log += f"{interaction.user.name} vs {opponent.name}\n\n"
    log += f"→ {interaction.user.name} の攻撃！ サイコロ({atk_dice}) → {opponent.name} に {damage_to_def} ダメージ！\n"
    log += f"→ {opponent.name} の反撃！ サイコロ({def_atk_dice}) → {interaction.user.name} に {damage_to_atk} ダメージ！\n\n"
    log += f"【最終HP】\n{interaction.user.name}：{atk_hp} HP\n{opponent.name}：{def_hp} HP\n"

    # 勝敗判定と記録
    if atk_hp > def_hp:
        result = f"**{interaction.user.name} の勝利！**"
        record_result(str(interaction.user.id), str(opponent.id))
    elif def_hp > atk_hp:
        result = f"**{opponent.name} の勝利！**"
        record_result(str(opponent.id), str(interaction.user.id))
    else:
        result = "**引き分け！**"  # 記録しない

    log += f"\n{result}"
    await interaction.response.send_message(log)

# 勝率確認コマンド用
from pvp_record import get_record

@bot.tree.command(name="pvp勝率", description="自分のPvP勝敗記録を確認します")
async def pvp_record(interaction: discord.Interaction):
    record = get_record(str(interaction.user.id))
    win = record["win"]
    lose = record["lose"]
    total = win + lose
    win_rate = round(win / total * 100, 1) if total > 0 else 0

    msg = (
        f"**{interaction.user.name} のPvP記録**\n"
        f"勝ち：{win}\n"
        f"負け：{lose}\n"
        f"勝率：{win_rate}%"
    )
    await interaction.response.send_message(msg, ephemeral=True)

# --- プレフィックスコマンド（参考） ---
@bot.command()
async def ping(ctx):
    await ctx.send("ぽん！")

# Bot起動
bot.run(os.environ["TOKEN"])
