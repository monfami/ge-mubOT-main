import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import os
import signal
import sys

# インポート
from commands.game_commands import GameCommands
from commands.aiueo_commands import AiueoCommands, AiueoManager, handle_message
from game_recruitment import GameRecruitment

# .envファイルを読み込む
load_dotenv()

# Intentsを修正してmessage_contentを有効化
intents = discord.Intents.default()
intents.message_content = True

# BOTの設定
bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"), intents=intents)

# 通知チャンネルID
NOTIFICATION_CHANNEL_ID = 1355874242457112638

# シグナルハンドラの設定
def signal_handler(sig, frame):
    """終了シグナルを受け取った時の処理"""
    print("シャットダウン信号を受け取りました。終了処理を開始します...")
    
    # 非同期関数を実行するための関数
    async def shutdown_notification():
        try:
            channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
            if channel:
                await channel.send("**BOTがシャットダウンします。**")
        except Exception as e:
            print(f"シャットダウン通知の送信中にエラーが発生しました: {e}")
        finally:
            await bot.close()
    
    # イベントループが利用可能であれば、そこで非同期関数を実行
    if bot.loop and bot.loop.is_running():
        bot.loop.create_task(shutdown_notification())
    else:
        # 直接終了
        sys.exit(0)

# シグナルハンドラを登録
signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # 終了シグナル

# BOT停止コマンドを追加
@bot.tree.command(name="stop", description="BOTを停止します (管理者専用)")
@app_commands.default_permissions(administrator=True)
async def stop_bot(interaction: discord.Interaction):
    """BOTを停止するコマンド (管理者専用)"""
    # 管理者権限チェック
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("このコマンドは管理者のみ使用できます。", ephemeral=True)
        return
    
    await interaction.response.send_message("BOTをシャットダウンします...", ephemeral=True)
    
    # シャットダウン通知と終了処理
    try:
        channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
        if channel:
            await channel.send(f"**BOTがシャットダウンします。** (実行者: {interaction.user.mention})")
    except Exception as e:
        print(f"シャットダウン通知の送信中にエラーが発生しました: {e}")
    finally:
        # BOTを終了
        await bot.close()

# Hypixel Worldリンク用コマンドを追加
@bot.tree.command(name="hypixel_world", description="Hypixel Worldのリンクを表示します")
async def hypixel_world(interaction: discord.Interaction):
    hypixel_url = "https://drive.google.com/drive/folders/18w1Y27UJJc_MMS8Yy8tgAc6Sv71A0s6M"
    
    embed = discord.Embed(
        title="Hypixel World リンク",
        description=f"Hypixel Worldは[こちら]({hypixel_url})からアクセスできます。",
        color=discord.Color.gold()
    )
    embed.add_field(name="URL", value=hypixel_url)
    embed.set_footer(text="Hypixel World - Minecraft Server Data")
    
    await interaction.response.send_message(embed=embed)

# メッセージイベントハンドラを追加
@bot.event
async def on_message(message):
    # AiueoManagerのメッセージハンドラを実行
    await handle_message(message)
    
    # コマンド処理を続行
    await bot.process_commands(message)

# セットアップコマンド - BOTのスラッシュコマンドとして提供
@bot.tree.command(name="setup", description="BOTの初期設定を行います（管理者のみ）")
@app_commands.default_permissions(administrator=True)
async def setup_command(interaction: discord.Interaction):
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
    # コマンドグループを追加
    game_commands = GameCommands()
    aiueo_commands = AiueoCommands()
    
    bot.tree.add_command(game_commands)
    bot.tree.add_command(aiueo_commands)
    
    await bot.tree.sync()  # スラッシュコマンドを同期
    print(f"BOTがログインしました: {bot.user}")
    
    # 起動通知メッセージを送信
    try:
        channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
        if channel:
            await channel.send("**BOTが起動しました。**")
    except Exception as e:
        print(f"起動通知の送信中にエラーが発生しました: {e}")

# トークンを.envから取得してBOTを起動
bot.run(os.getenv("DISCORD_BOT_TOKEN"))
