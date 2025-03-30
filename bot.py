import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

# .envファイルを読み込む
load_dotenv()

# Intentsを修正してmessage_contentを有効化
intents = discord.Intents.default()
intents.message_content = True

# BOTの設定
bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"), intents=intents)

# スラッシュコマンドの同期
@bot.event
async def on_ready():
    await bot.tree.sync()  # スラッシュコマンドを同期
    print(f"BOTがログインしました: {bot.user}")

# スラッシュコマンド: /game
@bot.tree.command(name="game", description="ゲームコマンドの説明を表示します")
async def game(interaction: discord.Interaction):
    game_message = """
    **BOTのゲームコマンド一覧**
    `/game` - このゲームコマンドの説明を表示します。
    `/ping` - BOTの応答速度を確認します。
    """
    await interaction.response.send_message(game_message)

# スラッシュコマンド: /ping
@bot.tree.command(name="ping", description="BOTの応答速度を確認します")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

# トークンを.envから取得してBOTを起動
bot.run(os.getenv("DISCORD_BOT_TOKEN"))
