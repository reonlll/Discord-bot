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

# 残高確認
@bot.tree.command(name="残高確認", description="自分のstarcoin残高を確認します")
async def check_balance(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    balance = get_balance(user_id)
    await interaction.response.send_message(
        f"{interaction.user.mention} の starcoin 残高：{balance} SC",
        ephemeral=True  # 自分にだけ表示
    )

@bot.tree.command(name="コイン付与", description="指定ユーザーにスターコインを付与します（管理者のみ）")
@app_commands.describe(user="付与する相手", amount="付与する金額")
@commands.has_permissions(administrator=True)
async def give_coin(interaction: discord.Interaction, user: discord.User, amount: int):
    add_balance(str(user.id), amount)
    await interaction.response.send_message(f"{user.mention} に {amount} SC を付与しました。")

# アイテム装備
@bot.tree.command(name="アイテム装備", description="指定したアイテムを装備します")
@app_commands.describe(name="装備するアイテム名")
async def item_set(interaction: discord.Interaction, name: str):
    user_id = str(interaction.user.id)
    set_equipment(user_id, "item", name)
    await interaction.response.send_message(f"アイテム「{name}」を装備しました！", ephemeral=True)

@bot.tree.command(name="ランキング", description="スターコイン残高ランキングを表示します")
async def coin_ranking(interaction: discord.Interaction):
    all_data = get_all_balances()
    if not all_data:
        await interaction.response.send_message("まだ誰もstarcoinを持っていません。", ephemeral=True)
        return

    sorted_data = sorted(all_data.items(), key=lambda x: x[1], reverse=True)
    message = "**スターコイン ランキング：**\n"
    for i, (user_id, balance) in enumerate(sorted_data[:10], start=1):
        user = await bot.fetch_user(int(user_id))
        message += f"{i}. {user.name}：{balance} SC\n"

    await interaction.response.send_message(message, ephemeral=True)

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
    
    import random
from pvp_stats import weapon_power, armor_defense

@bot.tree.command(name="pvp", description="指定した相手とPvPバトルします（運要素あり）")
@app_commands.describe(opponent="対戦相手")
async def pvp(interaction: discord.Interaction, opponent: discord.User):
    if opponent.id == interaction.user.id:
        await interaction.response.send_message("自分自身とは戦えません！", ephemeral=True)
        return

    # 装備取得
    atk_eq = get_equipment(interaction.user.id)
    def_eq = get_equipment(opponent.id)

    atk_power = weapon_power.get(atk_eq["weapon"], 5)
    atk_def = armor_defense.get(atk_eq["armor"], 2)

    def_power = weapon_power.get(def_eq["weapon"], 5)
    def_def = armor_defense.get(def_eq["armor"], 2)

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

    # 勝敗
    if atk_hp > def_hp:
        result = f"**{interaction.user.name} の勝利！**"
    elif def_hp > atk_hp:
        result = f"**{opponent.name} の勝利！**"
    else:
        result = "**引き分け！**"

    log += f"\n{result}"

    await interaction.response.send_message(log)

from pvp_record import record_result

# 勝敗処理のあとに追加
if atk_hp > def_hp:
    result = f"**{interaction.user.name} の勝利！**"
    record_result(str(interaction.user.id), str(opponent.id))
elif def_hp > atk_hp:
    result = f"**{opponent.name} の勝利！**"
    record_result(str(opponent.id), str(interaction.user.id))
else:
    result = "**引き分け！**"  # 記録しない
    
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
