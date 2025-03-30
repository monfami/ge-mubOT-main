import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

# .envファイルを読み込む
load_dotenv()

# BOTの設定
bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"), intents=discord.Intents.all())

@bot.event
async def on_ready():
    print(f"BOTがログインしました: {bot.user}")
    print("以下のURLでBOTをサーバーに招待できます:")
    print(f"https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=bot%20applications.commands")

@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    """サーバーに必要なロールを作成します"""
    guild = ctx.guild
    
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
    
    await ctx.send("\n".join(response) + "\nセットアップが完了しました！`/game recruit` コマンドでゲーム募集を始められます。")

# BOTを起動
bot.run(os.getenv("DISCORD_BOT_TOKEN"))
