import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import os

# インポート
from commands.game_commands import GameCommands
from game_recruitment import GameRecruitment

# .envファイルを読み込む
load_dotenv()

# Intentsを修正してmessage_contentを有効化
intents = discord.Intents.default()
intents.message_content = True

# BOTの設定
bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"), intents=intents)

# あいうえお機能の状態を管理する辞書（サーバーIDをキーとして使用）
aiueo_enabled = {}

# Hypixel Worldリンク用コマンドを追加
@bot.tree.command(name="hypixel_world", description="Hypixel Worldのリンクを表示します")
async def hypixel_world(interaction: discord.Interaction):
    """Hypixel Worldのリンクを表示します"""
    hypixel_url = "https://drive.google.com/drive/folders/18w1Y27UJJc_MMS8Yy8tgAc6Sv71A0s6M"
    
    embed = discord.Embed(
        title="Hypixel World リンク",
        description=f"Hypixel Worldは[こちら]({hypixel_url})からアクセスできます。",
        color=discord.Color.gold()
    )
    embed.add_field(name="URL", value=hypixel_url)
    embed.set_footer(text="Hypixel World - Minecraft Server Data")
    
    await interaction.response.send_message(embed=embed)

# aiueoコマンドを更新 - 設定パラメータを必須に変更
@bot.tree.command(name="aiueo", description="あいうえお応答機能を設定します")
@app_commands.describe(設定="「on」または「off」を指定してください")
async def aiueo(interaction: discord.Interaction, 設定: str):
    """あいうえお応答機能を設定するコマンド"""
    guild_id = str(interaction.guild_id)
    
    # パラメータの処理
    if 設定.lower() == "on":
        aiueo_enabled[guild_id] = True
        await interaction.response.send_message("あいうえお応答機能を **オン** にしました。\nチャットで「あいうえお」と発言すると「かきくけこ」と応答します。")
    elif 設定.lower() == "off":
        aiueo_enabled[guild_id] = False
        await interaction.response.send_message("あいうえお応答機能を **オフ** にしました。")
    else:
        await interaction.response.send_message("設定は `on` または `off` を指定してください。", ephemeral=True)

# メッセージイベントハンドラを追加
@bot.event
async def on_message(message):
    # BOT自身のメッセージは無視
    if message.author == bot.user:
        return
    
    # aiueo機能が有効な場合
    guild_id = str(message.guild.id) if message.guild else None
    if guild_id and aiueo_enabled.get(guild_id, False):
        # メッセージが「あいうえお」を含むか確認
        if "あいうえお" in message.content:
            await message.channel.send("かきくけこ")
    
    # コマンド処理を続行
    await bot.process_commands(message)

# セットアップコマンド - BOTのスラッシュコマンドとして提供
@bot.tree.command(name="setup", description="BOTの初期設定を行います（管理者のみ）")
@app_commands.default_permissions(administrator=True)
async def setup_command(interaction: discord.Interaction):
    """サーバーに必要なロールを作成します"""
    guild = interaction.guild
    
    # BOT操作ロールの作成
    admin_role_name = "BOT操作"
    existing_admin_role = discord.utils.get(guild.roles, name=admin_role_name)
    
    # BOT!ロールの作成
    bot_role_name = "BOT!"
    existing_bot_role = discord.utils.get(guild.roles, name=bot_role_name)
    
    response = []
    
    if existing_admin_role:
        response.append(f"`{admin_role_name}` ロールはすでに存在します。")
    else:
        try:
            # 目立つ色のロールを作成
            await guild.create_role(name=admin_role_name, colour=discord.Colour.blue(), 
                                   mentionable=True, 
                                   reason="ゲーム募集BOTのセットアップ")
            response.append(f"`{admin_role_name}` ロールを作成しました。このロールを持つユーザーはゲーム募集の管理ができます。")
        except:
            response.append(f"`{admin_role_name}` ロールの作成に失敗しました。BOTに必要な権限があるか確認してください。")
    
    if existing_bot_role:
        response.append(f"`{bot_role_name}` ロールはすでに存在します。")
    else:
        try:
            # BOT!ロールを作成
            await guild.create_role(name=bot_role_name, colour=discord.Colour.purple(), 
                                   mentionable=True, 
                                   reason="BOTの自由参加用ロール")
            response.append(f"`{bot_role_name}` ロールを作成しました。このロールを持つメンバーはすべてのゲームチャンネルに参加できます。")
        except:
            response.append(f"`{bot_role_name}` ロールの作成に失敗しました。BOTに必要な権限があるか確認してください。")
    
    response.append("セットアップが完了しました！`/game recruit` コマンドでゲーム募集を始められます。")
    
    await interaction.response.send_message("\n".join(response))

# スラッシュコマンドの同期
@bot.event
async def on_ready():
    # ゲームコマンドグループを追加
    game_commands = GameCommands()
    bot.tree.add_command(game_commands)
    
    await bot.tree.sync()  # スラッシュコマンドを同期
    print(f"BOTがログインしました: {bot.user}")

# トークンを.envから取得してBOTを起動
bot.run(os.getenv("DISCORD_BOT_TOKEN"))
