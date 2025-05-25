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

def get_job(user_id: int):
    try:
        with open("job.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get(str(user_id), {"name": "未設定", "hp": "不明", "skill": "なし"})
    except FileNotFoundError:
        return {"name": "未設定", "hp": "不明", "skill": "なし"}

職業一覧 = [
    app_commands.Choice(name="剣士", value="剣士"),
    app_commands.Choice(name="魔法使い", value="魔法使い"),
    app_commands.Choice(name="暗殺者", value="暗殺者"),
    app_commands.Choice(name="狙撃手", value="狙撃手"),
]

# Intents（メッセージ内容取得を有効に）
intents = discord.Intents.default()
intents.message_content = True

# BotとCommandTree初期化
bot = commands.Bot(command_prefix="!", intents=intents)
# PvP状態を保持する
active_battles = {}

# PvP状態クラス
class PvPBattleState:
    def __init__(self, player1_id, player2_id):
        self.player1_id = player1_id
        self.player2_id = player2_id
        self.hp = {
            player1_id: 100,
            player2_id: 100
        }
        self.turn = player1_id
        self.id = str(uuid.uuid4())

class PvPButtonView(View):
    def __init__(self, state, bot):
        super().__init__(timeout=60)
        self.state = state
        self.bot = bot

        self.attack_button = Button(label="攻撃する", style=discord.ButtonStyle.primary)
        self.attack_button.callback = self.attack_callback
        self.add_item(self.attack_button)

    async def attack_callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        if self.state.turn != user_id:
            await interaction.response.send_message("あなたのターンではありません！", ephemeral=True)
            return

        opponent_id = self.state.player2_id if self.state.turn == self.state.player1_id else self.state.player1_id
        damage = random.randint(10, 20)
        self.state.hp[opponent_id] -= damage

        if self.state.hp[opponent_id] <= 0:
            await interaction.response.edit_message(
                content=f"{interaction.user.name} が勝利しました！",
                view=None
            )
            del active_battles[self.state.id]
            return

        self.state.turn = opponent_id
        await interaction.response.edit_message(
            content=f"{interaction.user.name} の攻撃！ {damage} ダメージ！\n\n"
                    f"現在のHP：\n- {interaction.user.name}：{self.state.hp[user_id]}HP\n"
                    f"- 相手：{self.state.hp[opponent_id]}HP\n\n"
                    f"次は相手のターンです。",
            view=self
        )

# Bot起動時：スラッシュコマンドを同期
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ ログイン成功: {bot.user}")

# --- スラッシュコマンド ---

@bot.tree.command(name="ギルドカード", description="自分のスターコイン残高・職業・装備を表示します")
async def guild_card(interaction: discord.Interaction):
    # ユーザーのIDを文字列として取得
    user_id = str(interaction.user.id)
    
    # 残高、装備、職業データの取得
    balance = get_balance(user_id)
    eq = get_equipment(user_id)
    job = get_job(user_id) or {"name": "未設定", "hp": "不明", "skill": "なし"}
    
    # 辞書から各項目を取得
    job_name = job.get("name", "未設定")
    hp = job.get("hp", "不明")
    skill = job.get("skill", "なし")
    
    # 装備に基づく能力値（装備がない場合は「なし」）
    atk = weapon_power(eq["weapon"]) if eq.get("weapon") else "-"
    defense = armor_defense(eq["armor"]) if eq.get("armor") else "-"

    # 表示メッセージの作成
    message = (
        f"**{interaction.user.name} のギルドカード**\n"
        f"職業：{job_name} (HP：{hp} / 特性：{skill})\n"
        f"スターコイン：{balance} SC\n\n"
        f"[能力値]\n"
        f"攻撃力：{atk}\n"
        f"防御力：{defense}\n\n"
        f"[装備]\n"
        f"武器：{eq.get('weapon', 'なし')}\n"
        f"防具：{eq.get('armor', 'なし')}\n"
        f"アイテム：{eq.get('item', 'なし')}"
    )
    
    # メッセージを、コマンド実行者にのみ表示（ephemeral）
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

@bot.tree.command(name="pvp", description="PvPバトルを開始します")
@app_commands.describe(opponent="対戦相手")
async def pvp(interaction: discord.Interaction, opponent: discord.Member):
    if opponent.id == interaction.user.id:
        await interaction.response.send_message("自分とは戦えません。", ephemeral=True)
        return

    state = PvPBattleState(str(interaction.user.id), str(opponent.id))
    active_battles[state.id] = state

    view = PvPButtonView(state, bot)
    await interaction.response.send_message(
        f"{interaction.user.name} vs {opponent.name} のバトルが開始！\n"
        f"{interaction.user.name} のターンです。攻撃してください！",
        view=view
    )

JOB_FILE = "job.json"

def set_job(user_id: int, job_name: str):
    try:
        with open(JOB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}

    data[str(user_id)] = job_name

    with open(JOB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

職業データ = {
    "剣士": {"hp": 100, "skill": "なし"},
    "魔法使い": {"hp": 90, "skill": "必ず先制"},
    "暗殺者": {"hp": 85, "skill": "20%で攻撃回避"},
    "狙撃手": {"hp": 75, "skill": "20%でもう1ターン"}
}

@bot.tree.command(name="職業選択", description="指定したユーザーに職業を付与します（管理者専用）")
@app_commands.describe(user="職業を付与するユーザー", job="職業名")
@commands.has_permissions(administrator=True)
async def assign_job(interaction: discord.Interaction, user: discord.Member, job: str):
    if job not in 職業データ:
        await interaction.response.send_message("無効な職業名です。", ephemeral=True)
        return

    with open("job.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    data[str(user.id)] = {"name": job, **職業データ[job]}

    with open("job.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    await interaction.response.send_message(f"{user.display_name} に職業「{job}」を付与しました！", ephemeral=True)


# --- プレフィックスコマンド（参考） ---
@bot.command()
async def ping(ctx):
    await ctx.send("ぽん！")

# Bot起動
bot.run(os.environ["TOKEN"])
