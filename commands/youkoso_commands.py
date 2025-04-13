import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import logging
import sys
import datetime
from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv()

# デバッグのためのロガーを設定
logger = logging.getLogger('youkoso')
logger.setLevel(logging.DEBUG)

# コンソール出力用のハンドラを追加
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)  # INFO以上のレベルをコンソールに出力
console_format = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
console_handler.setFormatter(console_format)

# ログディレクトリの確認と作成
log_directory = os.getenv("LOG_DIRECTORY", "logs")
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

# ファイル出力用のハンドラ
youkoso_log_path = os.getenv("YOUKOSO_LOG_PATH", os.path.join(log_directory, "youkoso.log"))
file_handler = logging.FileHandler(youkoso_log_path, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_format = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')
file_handler.setFormatter(file_format)

# 両方のハンドラをロガーに追加
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# 既存のハンドラを削除（重複を防ぐため）
if logger.handlers:
    for handler in logger.handlers[:]:
        if isinstance(handler, logging.StreamHandler) and handler != console_handler and handler != file_handler:
            logger.removeHandler(handler)

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

# グローバル変数としてインスタンスを保持
youkoso_instance = None

# グローバルレベルでメンバー参加イベントを処理する関数
async def handle_member_join_global(member):
    """bot.pyから呼び出されるグローバルなメンバー参加ハンドラ"""
    try:
        logger.info(f"グローバルハンドラ: 新規メンバー参加 {member.name}#{member.discriminator}")
        
        # インスタンスが初期化されているか確認
        if youkoso_instance is None:
            logger.warning("youkoso_instanceがNoneです。WelcomeSettingsを直接使用します。")
            # 直接WelcomeSettingsを使ってメッセージ送信
            settings = WelcomeSettings()
            await send_welcome_message(member, settings)
        else:
            # 既存インスタンスを使ってメッセージ送信
            await youkoso_instance.handle_member_join(member)
    except Exception as e:
        logger.error(f"グローバルハンドラでエラー発生: {e}")
        import traceback
        traceback.print_exc()

# ようこそメッセージ送信関数（直接使用可能）
async def send_welcome_message(member, settings):
    """メンバーに対してようこそメッセージを送信する"""
    guild_id = member.guild.id
    
    # コンソールに通知
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n==================================================")
    print(f"⏰ 時刻: {current_time}")
    print(f"🎉 新規メンバー参加: {member.name}#{member.discriminator} (ID: {member.id})")
    print(f"サーバー: {member.guild.name} (ID: {member.guild.id})")
    print(f"参加日時: {member.joined_at}")
    print(f"アカウント作成日時: {member.created_at}")
    print(f"==================================================\n")
    
    # ようこそメッセージが有効かつチャンネルが設定されている場合
    if settings.is_enabled(guild_id):
        channel_id = settings.get_channel_id(guild_id)
        if channel_id:
            channel = member.guild.get_channel(channel_id)
            if channel:
                # ようこそメッセージを送信
                youtube_link = "https://www.youtube.com/channel/UCXn0LlFmWXr_rXBWPtD94vQ"
                
                # Embedオブジェクトを作成
                embed = discord.Embed(
                    title="🎉 新メンバー参加",
                    description=f"{member.mention}さん、動画班鯖へようこそ！ そして、[ちゃびーチャンネル]({youtube_link})登録してるかな?(圧)また、無法地帯サーバー(muhoutitaitekina.feathermc.gg)1.21.4に入ろう‼",
                    color=discord.Color.green()
                )
                
                try:
                    await channel.send(embed=embed)
                    logger.info(f"ようこそメッセージを送信しました: {member.name} -> {channel.name}")
                    return True
                except Exception as e:
                    logger.error(f"メッセージ送信エラー: {e}")
            else:
                logger.error(f"チャンネルが見つかりません: ID {channel_id}")
        else:
            logger.error("チャンネルIDが設定されていません")
    else:
        logger.info(f"サーバー {member.guild.name} ではようこそメッセージが無効です")
    
    return False

# ようこそコマンドのグループ
class YoukosoCommands(app_commands.Group):
    def __init__(self):
        super().__init__(name="youkoso", description="ようこそメッセージの設定")
        self.welcome_settings = WelcomeSettings()
        logger.info("YoukosoCommandsクラスが初期化されました")
    
    # メンバー参加イベントのハンドラ
    async def handle_member_join(self, member):
        """メンバー参加時の処理"""
        await send_welcome_message(member, self.welcome_settings)

    # ようこそコマンドの設定（単一コマンドに統合）
    @app_commands.command(name="setup", description="ようこそメッセージの設定を行います")
    @app_commands.describe(
        status="ようこそメッセージの有効/無効を設定します (on/off)",
        channel="ようこそメッセージを送信するチャンネルを指定します"
    )
    @app_commands.default_permissions(administrator=True)
    async def youkoso_setup(self, interaction: discord.Interaction, status: str, channel: discord.TextChannel):
        # statusを小文字に統一して処理
        status = status.lower()
        
        if status not in ["on", "off"]:
            await interaction.response.send_message("statusには 'on' または 'off' を指定してください。", ephemeral=True)
            return
            
        # welcome_settingsを取得
        welcome_settings = self.welcome_settings
        
        if status == "on":
            # 設定を保存
            welcome_settings.set_enabled(interaction.guild.id, True)
            welcome_settings.set_channel(interaction.guild.id, channel.id)
            
            # 成功メッセージを送信
            await interaction.response.send_message(
                f"ようこそメッセージを **オン** にしました。\n"
                f"送信先チャンネル: {channel.mention}"
            )
        else:  # status == "off"
            # 設定を保存（チャンネルはそのまま保持）
            welcome_settings.set_enabled(interaction.guild.id, False)
            
            # 成功メッセージを送信
            await interaction.response.send_message("ようこそメッセージを **オフ** にしました。")

def setup_youkoso_commands(bot):
    """ようこそコマンドをbotに登録する関数"""
    global youkoso_instance
    
    # YoukosoCommandsのインスタンスを作成
    youkoso_group = YoukosoCommands()
    youkoso_instance = youkoso_group
    
    # コマンドをbotに追加
    bot.tree.add_command(youkoso_group)
    
    # メンバー参加イベントハンドラを設定
    @bot.event
    async def on_member_join(member):
        await youkoso_instance.handle_member_join(member)
    
    logger.info("ようこそコマンドを登録しました")
