import discord
from discord import app_commands
# 相対インポートを絶対インポートに変更
from game_recruitment import GameRecruitment
from views.public_view import PublicJoinView
from views.management_view import GameManagementView
from views.member_view import GameMemberView

# ゲームコマンドグループ
class GameCommands(app_commands.Group):
    def __init__(self):
        super().__init__(name="game", description="ゲーム関連のコマンド")
    
    # 汎用的な募集コマンド - 人数を必須項目に変更
    @app_commands.command(name="recruit", description="ゲームの募集を作成します")
    @app_commands.describe(
        ゲーム名="募集したいゲームの名前",
        人数="募集する最大人数"
    )
    async def recruit(self, interaction: discord.Interaction, ゲーム名: str, 人数: int):
        if 人数 < 2 or 人数 > 16:
            await interaction.response.send_message("募集人数は2人から16人までにしてください。", ephemeral=True)
            return
            
        await interaction.response.defer(ephemeral=True)
        
        # プライベートチャンネルを作成
        text_channel, voice_channel, category, recruitment_id = await GameRecruitment.create_recruitment(
            interaction, ゲーム名, 人数
        )
        
        # 募集情報を保存した後、ビューを作成
        game_info_embed = discord.Embed(
            title=f"{ゲーム名}の募集",
            description=f"ホスト: {interaction.user.mention}\n"
                       f"参加人数: 1/{人数}",
            color=discord.Color.blue()
        )
        
        # 管理者用のビュー
        host_view = GameManagementView(recruitment_id, 人数)
        await text_channel.send(embed=game_info_embed, view=host_view)
        
        # 参加者用のビュー（退出ボタン付き）
        member_view = GameMemberView(recruitment_id)
        await text_channel.send(
            f"**ようこそ {ゲーム名} の募集チャンネルへ！**\n\n"
            f"このチャンネルはゲームの参加者専用です。\n"
            f"ボイスチャットはこちら: {voice_channel.mention}\n\n"
            f"ゲームが終了したら、ホストまたは管理者が「ゲームを終了する」ボタンを押すことでチャンネルを削除できます。", 
            view=member_view
        )
        
        # 公開募集メッセージを作成
        public_embed = discord.Embed(
            title=f"🎮 {ゲーム名}の募集",
            description=f"{interaction.user.display_name}さんが、{ゲーム名}の参加者を、{人数}人募集しました。参加したい方は、下のボタンから参加してください。\n\n参加人数: 1/{人数}",
            color=discord.Color.green()
        )
        public_view = PublicJoinView(recruitment_id)
        
        # 公開メッセージを保存
        public_message = await interaction.channel.send(embed=public_embed, view=public_view)
        
        # 募集情報に公開メッセージIDを追加
        recruitment = GameRecruitment.recruitments.get(recruitment_id)
        if recruitment:
            recruitment["public_message_id"] = public_message.id
            recruitment["public_channel_id"] = interaction.channel_id
        
        await interaction.followup.send(
            f"{ゲーム名}の募集を開始しました！\n"
            f"テキストチャンネル: {text_channel.mention}\n"
            f"ボイスチャンネル: {voice_channel.mention}", 
            ephemeral=True
        )
