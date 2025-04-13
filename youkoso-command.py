import discord
from discord.ext import commands
from discord import app_commands
import json
import os

# ようこそ機能の設定を管理するクラス
class WelcomeSettings:
    def __init__(self):
        log_directory = os.getenv("LOG_DIRECTORY", "logs")
        self.config_file = os.getenv("WELCOME_CONFIG_PATH", os.path.join(log_directory, "welcome_config.json"))
        self.settings = self._load_settings()
    
    def _load_settings(self):
        # 設定ファイルが存在しない場合は空の設定を作成
        if not os.path.exists(self.config_file):
            default_settings = {}
            self._save_settings(default_settings)
            return default_settings
        
        # 設定ファイルを読み込む
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"設定ファイルの読み込みに失敗しました: {e}")
            return {}
    
    def _save_settings(self, settings):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"設定ファイルの保存に失敗しました: {e}")
    
    def is_enabled(self, guild_id):
        guild_id = str(guild_id)  # JSONのキーは文字列
        if guild_id in self.settings:
            return self.settings[guild_id].get('enabled', False)
        return False
    
    def get_channel_id(self, guild_id):
        guild_id = str(guild_id)
        if guild_id in self.settings:
            return self.settings[guild_id].get('channel_id')
        return None
    
    def set_enabled(self, guild_id, enabled):
        guild_id = str(guild_id)
        if guild_id not in self.settings:
            self.settings[guild_id] = {}
        self.settings[guild_id]['enabled'] = enabled
        self._save_settings(self.settings)
    
    def set_channel(self, guild_id, channel_id):
        guild_id = str(guild_id)
        if guild_id not in self.settings:
            self.settings[guild_id] = {'enabled': False}
        self.settings[guild_id]['channel_id'] = channel_id
        self._save_settings(self.settings)

# ようこそコマンドのグループ
class YoukosoCommands(app_commands.Group):
    def __init__(self):
        super().__init__(name="youkoso", description="ようこそメッセージの設定")
        self.welcome_settings = WelcomeSettings()
    
    # メンバー参加イベントのハンドラ
    async def handle_member_join(self, member):
        guild_id = member.guild.id
        
        # ようこそメッセージが有効かつチャンネルが設定されている場合
        if self.welcome_settings.is_enabled(guild_id):
            channel_id = self.welcome_settings.get_channel_id(guild_id)
            if channel_id:
                channel = member.guild.get_channel(channel_id)
                if channel:
                    # ようこそメッセージを送信
                    youtube_link = "https://www.youtube.com/channel/UCXn0LlFmWXr_rXBWPtD94vQ"
                    welcome_message = f"{member.mention}さん、動画班鯖へようこそ！ そして、[ちゃびーチャンネル]({youtube_link})を、登録してるかな?(圧)"
                    
                    # Embedオブジェクトを作成
                    embed = discord.Embed(
                        description=welcome_message,
                        color=discord.Color.green()
                    )
                    
                    await channel.send(embed=embed)

# ようこそコマンドの設定（有効/無効の切り替え）
@app_commands.command(name="on", description="ようこそメッセージを有効にします")
@app_commands.describe(channel="ようこそメッセージを送信するチャンネル")
@app_commands.default_permissions(administrator=True)
async def youkoso_on(interaction: discord.Interaction, channel: discord.TextChannel):
    # 親グループからWelcomeSettingsを取得
    welcome_settings = interaction.client.get_command("youkoso").welcome_settings
    
    # 設定を保存
    welcome_settings.set_channel(interaction.guild_id, channel.id)
    welcome_settings.set_enabled(interaction.guild_id, True)
    
    await interaction.response.send_message(f"ようこそメッセージを有効にしました。送信先チャンネル: {channel.mention}", ephemeral=True)

# ようこそコマンドの設定（無効化）
@app_commands.command(name="off", description="ようこそメッセージを無効にします")
@app_commands.default_permissions(administrator=True)
async def youkoso_off(interaction: discord.Interaction):
    # 親グループからWelcomeSettingsを取得
    welcome_settings = interaction.client.get_command("youkoso").welcome_settings
    
    # 設定を保存
    welcome_settings.set_enabled(interaction.guild_id, False)
    
    await interaction.response.send_message("ようこそメッセージを無効にしました。", ephemeral=True)

# コマンドの登録
def setup_youkoso_commands(bot):
    youkoso_group = YoukosoCommands()
    youkoso_group.add_command(youkoso_on)
    youkoso_group.add_command(youkoso_off)
    bot.tree.add_command(youkoso_group)
    
    # メンバー参加イベントのハンドラを登録
    @bot.event
    async def on_member_join(member):
        await youkoso_group.handle_member_join(member)
