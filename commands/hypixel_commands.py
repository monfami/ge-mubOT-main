import discord
from discord.ext import commands
from discord import app_commands
import os

class HypixelCommands:
    """Hypixel関連のコマンドを管理するクラス"""
    
    def __init__(self):
        # デフォルトのURLを設定
        self.hypixel_url = os.getenv("HYPIXEL_WORLD_URL", 
                                    "https://drive.google.com/drive/folders/18w1Y27UJJc_MMS8Yy8tgAc6Sv71A0s6M")
    
    @app_commands.command(name="hypixel_world", description="Hypixel Worldのリンクを表示します")
    async def hypixel_world(self, interaction: discord.Interaction):
        """Hypixel Worldのリンクを表示するコマンド"""
        embed = discord.Embed(
            title="Hypixel World リンク",
            description=f"Hypixel Worldは[こちら]({self.hypixel_url})からアクセスできます。",
            color=discord.Color.gold()
        )
        embed.add_field(name="URL", value=self.hypixel_url)
        embed.set_footer(text="Hypixel World - Minecraft Server Data")
        
        await interaction.response.send_message(embed=embed)

def setup_hypixel_commands(bot):
    """Hypixel関連コマンドをbotに登録する関数"""
    hypixel_commands = HypixelCommands()
    
    # コマンドを直接登録
    bot.tree.add_command(hypixel_commands.hypixel_world)
    
    print("Hypixelコマンドを登録しました")
