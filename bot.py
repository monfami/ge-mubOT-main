import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import os
import signal
import sys
import threading
from flask import Flask, jsonify

# インポート
from commands.game_commands import GameCommands
from commands.aiueo_commands import AiueoCommands, AiueoManager, handle_message
from commands.satuei import SatueiCommands
from commands.youkoso_commands import setup_youkoso_commands  # ようこそコマンドをインポート
from commands.yakudati_commands import setup_yakudati_commands  # 役立ちメンバーコマンドをインポート
from commands.admin_commands import setup_admin_commands  # 管理者コマンドをインポート
from commands.hypixel_commands import setup_hypixel_commands  # Hypixelコマンドをインポート
from commands.auth_commands import setup_auth_commands  # 認証コマンドをインポート

# .envファイルを読み込む
load_dotenv()

# Intentsを修正して必要な権限をすべて有効化
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # メンバーイベントを監視するために必要
intents.guilds = True   # サーバー関連イベントを監視するために必要

# BOTの設定
command_prefix = os.getenv("COMMAND_PREFIX", "!")
bot = commands.Bot(command_prefix=commands.when_mentioned_or(command_prefix), intents=intents)

# 通知チャンネルID
NOTIFICATION_CHANNEL_ID = int(os.getenv("NOTIFICATION_CHANNEL_ID", 0))

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

# メッセージイベントハンドラを追加
@bot.event
async def on_message(message):
    # AiueoManagerのメッセージハンドラを実行
    await handle_message(message)
    
    # コマンド処理を続行
    await bot.process_commands(message)

# メッセージイベントハンドラを追加

# スラッシュコマンドの同期
@bot.event
async def on_ready():
    # コマンドグループを追加
    game_commands = GameCommands()
    aiueo_commands = AiueoCommands()
    satuei_commands = SatueiCommands()
    
    bot.tree.add_command(game_commands)
    bot.tree.add_command(aiueo_commands)
    bot.tree.add_command(satuei_commands)
    
    # ようこそコマンドをセットアップ
    setup_youkoso_commands(bot)
    
    # 役立ちメンバーコマンドをセットアップ
    setup_yakudati_commands(bot)
    
    # 管理者コマンドをセットアップ
    setup_admin_commands(bot, NOTIFICATION_CHANNEL_ID)
    
    # Hypixelコマンドをセットアップ
    setup_hypixel_commands(bot)
    
    # 認証コマンドをセットアップ
    auth_system = setup_auth_commands(bot)
    
    await bot.tree.sync()  # スラッシュコマンドを同期
    print(f"BOTがログインしました: {bot.user}")
    print(f"参加サーバー数: {len(bot.guilds)}")
    print(f"インテント設定: members={intents.members}, guilds={intents.guilds}, message_content={intents.message_content}")
    
    # 起動通知メッセージを送信
    try:
        channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
        if channel:
            await channel.send("**BOTが起動しました。**")
    except Exception as e:
        print(f"起動通知の送信中にエラーが発生しました: {e}")

# グローバルに新規参加者イベントを設定（冗長化のため）
@bot.event
async def on_member_join(member):
    print(f"\n==== BOTコアレベルでメンバー参加検知 ====")
    print(f"参加メンバー: {member.name}#{member.discriminator} (ID: {member.id})")
    print(f"サーバー: {member.guild.name}")
    print(f"参加時刻: {member.joined_at}")
    print(f"======================================\n")
    
    # youkoso_commandsモジュールの処理を呼び出す
    from commands.youkoso_commands import handle_member_join_global
    await handle_member_join_global(member)

# Flask アプリケーションの設定
app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "message": "Discord bot is running"
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy"
    })

# Flaskサーバーを別スレッドで実行する関数
def run_flask_app():
    # Renderが提供するPORTを使用するか、デフォルトで8080を使用
    port = int(os.getenv("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# Flaskサーバーを別スレッドで起動
flask_thread = threading.Thread(target=run_flask_app)
flask_thread.daemon = True  # メインプログラムが終了したら一緒に終了
flask_thread.start()

# トークンを.envから取得してBOTを起動
bot.run(os.getenv("DISCORD_BOT_TOKEN"))
