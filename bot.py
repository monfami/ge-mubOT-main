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
from commands.satuei import SatueiCommands
from game_recruitment import GameRecruitment
from youkoso_command import setup_youkoso_commands  # ようこそコマンドをインポート
from yakudati_command import setup_yakudati_commands  # 役立ちメンバーコマンドをインポート
from gas_integration import AuthSystem, AuthView  # 認証システムをインポート

# .envファイルを読み込む
load_dotenv()

# Intentsを修正して必要な権限をすべて有効化
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # メンバーイベントを監視するために必要
intents.guilds = True   # サーバー関連イベントを監視するために必要

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

# 認証システムのインスタンスを作成
auth_system = AuthSystem()

# 認証コマンドを追加
@bot.tree.command(name="ninnsyou", description="サーバー認証を行うためのボタンを設置します")
@app_commands.describe(role="認証後に付与するロール")
@app_commands.default_permissions(administrator=True)
async def setup_auth(interaction: discord.Interaction, role: discord.Role):
    """認証ボタンを設置するコマンド (管理者専用)"""
    # 管理者権限チェック
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("このコマンドは管理者のみ使用できます。", ephemeral=True)
        return
    
    # 認証メッセージを作成
    embed = discord.Embed(
        title="サーバー認証",
        description=f"下のボタンを押して認証を完了してください。\n認証後は {role.mention} ロールが付与されます。",
        color=discord.Color.blue()
    )
    
    # 認証ボタンビューを作成
    view = AuthView(auth_system, role.id)
    
    await interaction.response.send_message(embed=embed, view=view)

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
    
    # youkoso_commandモジュールの処理を呼び出す
    from youkoso_command import handle_member_join_global
    await handle_member_join_global(member)

# トークンを.envから取得してBOTを起動
bot.run(os.getenv("DISCORD_BOT_TOKEN"))
