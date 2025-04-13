import discord
from discord.ext import commands
from discord import app_commands
import os

class AdminCommands:
    """管理者用コマンドを管理するクラス"""
    
    def __init__(self, bot, notification_channel_id):
        self.bot = bot
        self.notification_channel_id = notification_channel_id
    
    @app_commands.command(name="stop", description="BOTを停止します (管理者専用)")
    @app_commands.default_permissions(administrator=True)
    async def stop_bot(self, interaction: discord.Interaction):
        """BOTを停止するコマンド (管理者専用)"""
        # 管理者権限チェック
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("このコマンドは管理者のみ使用できます。", ephemeral=True)
            return
        
        await interaction.response.send_message("BOTをシャットダウンします...", ephemeral=True)
        
        # シャットダウン通知と終了処理
        try:
            channel = self.bot.get_channel(self.notification_channel_id)
            if channel:
                await channel.send(f"**BOTがシャットダウンします。** (実行者: {interaction.user.mention})")
        except Exception as e:
            print(f"シャットダウン通知の送信中にエラーが発生しました: {e}")
        finally:
            # BOTを終了
            await self.bot.close()
    
    @app_commands.command(name="setup", description="BOTの初期設定を行います（管理者のみ）")
    @app_commands.default_permissions(administrator=True)
    async def setup_command(self, interaction: discord.Interaction):
        """BOTの初期設定を行うコマンド (管理者専用)"""
        guild = interaction.guild
        
        # BOT操作ロールの作成
        admin_role_name = os.getenv("ADMIN_ROLE_NAME", "BOT操作")
        existing_admin_role = discord.utils.get(guild.roles, name=admin_role_name)
        
        # BOT!ロールの作成
        bot_role_name = os.getenv("BOT_ROLE_NAME", "BOT!")
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

def setup_admin_commands(bot, notification_channel_id):
    """管理者コマンドをbotに登録する関数"""
    admin_commands = AdminCommands(bot, notification_channel_id)
    
    # コマンドを直接登録
    bot.tree.add_command(admin_commands.stop_bot)
    bot.tree.add_command(admin_commands.setup_command)
    
    print("管理者コマンドを登録しました")
