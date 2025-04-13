import discord
from discord.ext import commands
from discord import app_commands
from commands.gas_integration import AuthSystem, AuthView

class AuthCommands:
    """認証関連のコマンドを管理するクラス"""
    
    def __init__(self, auth_system):
        self.auth_system = auth_system
    
    @app_commands.command(name="ninnsyou", description="サーバー認証を行うためのボタンを設置します")
    @app_commands.describe(role="認証後に付与するロール")
    @app_commands.default_permissions(administrator=True)
    async def setup_auth(self, interaction: discord.Interaction, role: discord.Role):
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
        view = AuthView(self.auth_system, role.id)
        
        await interaction.response.send_message(embed=embed, view=view)

def setup_auth_commands(bot):
    """認証関連コマンドをbotに登録する関数"""
    # 認証システムのインスタンスを作成
    auth_system = AuthSystem()
    
    # コマンドクラスのインスタンスを作成
    auth_commands = AuthCommands(auth_system)
    
    # コマンドを直接登録
    bot.tree.add_command(auth_commands.setup_auth)
    
    print("認証コマンドを登録しました")
    
    # 認証システムのインスタンスを返す（他の場所で使用できるように）
    return auth_system
