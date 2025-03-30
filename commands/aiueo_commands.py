import discord
from discord import app_commands

class AiueoManager:
    """五十音応答機能を管理するクラス"""
    
    # サーバーごとの有効/無効状態を管理
    enabled_guilds = {}
    
    # 五十音の応答パターンを定義
    patterns = {
        "あいうえお": "かきくけこ",
        "かきくけこ": "さしすせそ",
        "さしすせそ": "たちつてと",
        "たちつてと": "なにぬねの",
        "なにぬねの": "はひふへほ",
        "はひふへほ": "まみむめも",
        "まみむめも": "やゆよ",
        "やゆよ": "らりるれろ",
        "らりるれろ": "わをん"
    }
    
    @classmethod
    def is_enabled(cls, guild_id):
        """指定されたサーバーで機能が有効かどうかを返す"""
        return cls.enabled_guilds.get(str(guild_id), False)
    
    @classmethod
    def enable(cls, guild_id):
        """指定されたサーバーで機能を有効にする"""
        cls.enabled_guilds[str(guild_id)] = True
    
    @classmethod
    def disable(cls, guild_id):
        """指定されたサーバーで機能を無効にする"""
        cls.enabled_guilds[str(guild_id)] = False
    
    @classmethod
    def get_response(cls, message_content):
        """メッセージに対応する応答を返す（なければNone）"""
        content = message_content.strip()
        return cls.patterns.get(content)
    
    @classmethod
    def get_patterns_description(cls):
        """応答パターンの説明文を生成"""
        description = ""
        for trigger, response in cls.patterns.items():
            description += f"「{trigger}」→「{response}」\n"
        return description

class AiueoCommands(app_commands.Group):
    def __init__(self):
        super().__init__(name="aiueo", description="五十音応答機能関連のコマンド")
    
    @app_commands.command(name="set", description="五十音応答機能の設定をします")
    @app_commands.describe(設定="「on」または「off」を指定してください")
    async def set_aiueo(self, interaction: discord.Interaction, 設定: str):
        """五十音応答機能の設定を変更するコマンド"""
        guild_id = interaction.guild_id
        
        # パラメータの処理
        if 設定.lower() == "on":
            AiueoManager.enable(guild_id)
            
            # 応答パターンを整形して表示
            pattern_description = AiueoManager.get_patterns_description()
            
            embed = discord.Embed(
                title="五十音応答機能をオンにしました",
                description="チャットで五十音の言葉を送信すると、続きの音で応答します。",
                color=discord.Color.green()
            )
            embed.add_field(name="応答パターン", value=pattern_description, inline=False)
            
            await interaction.response.send_message(embed=embed)
        elif 設定.lower() == "off":
            AiueoManager.disable(guild_id)
            await interaction.response.send_message("五十音応答機能を **オフ** にしました。")
        else:
            await interaction.response.send_message("設定は `on` または `off` を指定してください。", ephemeral=True)

# メッセージイベント処理
async def handle_message(message):
    """メッセージが五十音パターンに一致するか確認し、応答する"""
    # BOT自身のメッセージは無視
    if message.author.bot:
        return
    
    # サーバーメッセージでない場合は無視
    if not message.guild:
        return
    
    # 機能が有効でない場合は無視
    if not AiueoManager.is_enabled(message.guild.id):
        return
    
    # メッセージが五十音パターンに一致するか確認
    response = AiueoManager.get_response(message.content)
    if response:
        await message.channel.send(response)
