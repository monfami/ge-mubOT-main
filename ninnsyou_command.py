import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import uuid

# 認証用データとサーバー情報を管理するファイル
VERIFICATION_DATA_FILE = 'verification_data.json'
USER_SERVER_DATA_FILE = 'user_server_data.json'

# 認証データを管理する辞書
verification_data = {}

AUTH_SERVER_URL = "https://your-app-name.onrender.com"  # RenderのURLに置き換え

# ユーザーごとのサーバー情報を記録する関数
def log_user_server_data(user_id: int, guild: discord.Guild):
    """ユーザーが参加しているサーバー情報を記録する"""
    if not os.path.exists(USER_SERVER_DATA_FILE):
        user_server_data = {}
    else:
        with open(USER_SERVER_DATA_FILE, 'r', encoding='utf-8') as f:
            user_server_data = json.load(f)

    user_id_str = str(user_id)
    if user_id_str not in user_server_data:
        user_server_data[user_id_str] = []

    # サーバー情報を追加（重複を防ぐ）
    guild_info = {"guild_id": guild.id, "guild_name": guild.name}
    if guild_info not in user_server_data[user_id_str]:
        user_server_data[user_id_str].append(guild_info)

    # ファイルに保存
    with open(USER_SERVER_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(user_server_data, f, ensure_ascii=False, indent=4)

class VerificationView(discord.ui.View):
    def __init__(self, role: discord.Role):
        super().__init__(timeout=None)
        self.role = role

    @discord.ui.button(label="認証する", style=discord.ButtonStyle.green, custom_id="verify_button")
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """認証ボタンが押されたときの処理"""
        user = interaction.user
        verification_id = str(uuid.uuid4())  # 一意の認証IDを生成
        verification_data[verification_id] = {"user_id": user.id, "role_id": self.role.id, "guild_id": interaction.guild.id}

        # 認証データを認証サーバーに送信
        async with interaction.client.session.post(f"{AUTH_SERVER_URL}/add_verification", json={
            "verification_id": verification_id,
            "user_id": user.id,
            "role_id": self.role.id,
            "guild_id": interaction.guild.id
        }) as response:
            if response.status != 200:
                await interaction.response.send_message("認証サーバーへの登録に失敗しました。", ephemeral=True)
                return

        # DMを送信
        try:
            dm_channel = await user.create_dm()
            verification_url = f"{AUTH_SERVER_URL}/verify/{verification_id}"
            await dm_channel.send(
                f"{user.mention} さん、以下のリンクをクリックして認証を完了してください:\n{verification_url}"
            )
            await interaction.response.send_message("認証用のリンクをDMで送信しました！", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("DMを送信できませんでした。DMを有効にしてください。", ephemeral=True)

async def handle_verification(verification_id: str, bot: commands.Bot):
    """認証が完了したときに呼び出される関数"""
    if verification_id not in verification_data:
        return False  # 無効な認証ID

    data = verification_data.pop(verification_id)
    user_id = data["user_id"]
    role_id = data["role_id"]
    guild_id = data["guild_id"]

    guild = bot.get_guild(guild_id)
    if not guild:
        return False

    member = guild.get_member(user_id)
    role = guild.get_role(role_id)

    if member and role:
        try:
            await member.add_roles(role)
            log_user_server_data(user_id, guild)  # サーバー情報を記録
            return True
        except discord.Forbidden:
            return False
    return False

class NinnsyouCommands(app_commands.Group):
    def __init__(self):
        super().__init__(name="ninnsyou", description="認証コマンド")

    @app_commands.command(name="panel", description="認証パネルを作成します")
    @app_commands.describe(channel="認証パネルを送信するチャンネル", role="認証後に付与するロール")
    async def create_panel(self, interaction: discord.Interaction, channel: discord.TextChannel, role: discord.Role):
        """認証パネルを作成するコマンド"""
        embed = discord.Embed(
            title="認証パネル",
            description="以下のボタンをクリックして認証を完了してください。",
            color=discord.Color.blue()
        )
        embed.set_footer(text="認証を完了すると指定されたロールが付与されます。")

        view = VerificationView(role)
        await channel.send(embed=embed, view=view)
        await interaction.response.send_message(f"{channel.mention} に認証パネルを作成しました！", ephemeral=True)

def setup_ninnsyou_commands(bot):
    ninnsyou_group = NinnsyouCommands()
    bot.tree.add_command(ninnsyou_group)
