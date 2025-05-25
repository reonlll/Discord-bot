import discord
from discord.ext import commands
from discord import app_commands
import os
import json
import random
import uuid
import random
from discord.ui import View, Button

from currency import get_balance, add_balance, subtract_balance, get_all_balances
from equipment import get_equipment, set_equipment
from pvp_record import get_record, record_result
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

EQUIP_FILE = "equipment.json"

def save_equipment(user_id, weapon=None, armor=None, item=None):
    if os.path.exists(EQUIP_FILE):
        with open(EQUIP_FILE, "r") as f:
            data = json.load(f)
    else:
        data = {}

    user_id = str(user_id)
    if user_id not in data:
        data[user_id] = {}

    if weapon:
        data[user_id]["weapon"] = weapon
    if armor:
        data[user_id]["armor"] = armor
    if item:
        data[user_id]["item"] = item

    with open(EQUIP_FILE, "w") as f:
        json.dump(data, f, indent=4)

class EquipView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=120)
        self.user_id = user_id

        self.weapon_select = discord.ui.Select(
            placeholder="武器を選んでください",
            options=[
                discord.SelectOption(label="木の剣", description="攻撃力1"),
                discord.SelectOption(label="鉄の剣", description="攻撃力2"),
                discord.SelectOption(label="炎の剣", description="攻撃力3"),
            ],
            custom_id="weapon_select",
        )
        self.weapon_select.callback = self.select_callback
        self.add_item(self.weapon_select)

        self.armor_select = discord.ui.Select(
            placeholder="防具を選んでください",
            options=[
                discord.SelectOption(label="布の服", description="防御力1"),
                discord.SelectOption(label="鉄の鎧", description="防御力2"),
                discord.SelectOption(label="ドラゴンアーマー", description="防御力3"),
            ],
            custom_id="armor_select",
        )
        self.armor_select.callback = self.select_callback
        self.add_item(self.armor_select)

        self.item_select = discord.ui.Select(
            placeholder="アイテムを選んでください",
            options=[
                discord.SelectOption(label="回復薬", description="HP30回復"),
                discord.SelectOption(label="爆弾", description="敵に20ダメージ"),
                discord.SelectOption(label="毒消し", description="状態異常解除"),
            ],
            custom_id="item_select",
        )
        self.item_select.callback = self.select_callback
        self.add_item(self.item_select)

    async def select_callback(self, interaction: discord.Interaction):
        selected = interaction.data["values"][0]
        cid = interaction.data["custom_id"]

        if interaction.user.id != self.user_id:
            await interaction.response.send_message("これはあなたの装備メニューではありません。", ephemeral=True)
            return

        if cid == "weapon_select":
            save_equipment(self.user_id, weapon=selected)
            await interaction.response.send_message(f"**武器**を **{selected}** に装備しました。", ephemeral=True)
        elif cid == "armor_select":
            save_equipment(self.user_id, armor=selected)
            await interaction.response.send_message(f"**防具**を **{selected}** に装備しました。", ephemeral=True)
        elif cid == "item_select":
            save_equipment(self.user_id, item=selected)
            await interaction.response.send_message(f"**アイテム**を **{selected}** に装備しました。", ephemeral=True)

@bot.tree.command(name="装備", description="武器・防具・アイテムを装備します")
async def equip(interaction: discord.Interaction):
    view = EquipView(interaction.user.id)
    await interaction.response.send_message("装備を選んでください：", view=view, ephemeral=True)


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

@bot.tree.command(name="残高一覧", description="全ユーザーのstarcoin残高を表示します（管理者のみ）")
@app_commands.checks.has_permissions(administrator=True)
async def list_all_balances(interaction: discord.Interaction):
    try:
        with open("coin.json", "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        await interaction.response.send_message("残高データが見つかりません。", ephemeral=True)
        return

    if not data:
        await interaction.response.send_message("ユーザーの残高情報がありません。", ephemeral=True)
        return

    msg = "**全ユーザーの残高一覧**\n"
    for user_id, info in data.items():
        user = await bot.fetch_user(int(user_id))
        coin = info.get("coin", 0)
        msg += f"{user.name}：{coin} SC\n"

    await interaction.response.send_message(msg, ephemeral=True)


# --- プレフィックスコマンド（参考） ---
@bot.command()
async def ping(ctx):
    await ctx.send("ぽん！")

# Bot起動
bot.run(os.environ["TOKEN"])
