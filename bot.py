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
