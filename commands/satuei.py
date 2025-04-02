import discord
from discord import app_commands
from discord.ui import Button, View
import datetime
from typing import Optional, List
import asyncio

# 通知を送信するチャンネルID
ANNOUNCEMENT_CHANNEL_ID = 1356938207664537668  # 撮影開始・終了の通知チャンネル
PARTICIPANTS_CHANNEL_ID = 1356941201554673735  # 参加者向け通知チャンネル

class EndSatueiButton(Button):
    """撮影を終了するボタン"""
    def __init__(self, role_id: int, participants: List[int]):
        super().__init__(
            style=discord.ButtonStyle.danger,
            label="撮影を終了する",
            custom_id="end_satuei"
        )
        self.role_id = role_id
        self.participants = participants
    
    async def callback(self, interaction: discord.Interaction):
        # 管理者か撮影主催者のみ終了可能
        if not interaction.user.guild_permissions.administrator and interaction.user.id != self.view.owner_id:
            await interaction.response.send_message("このボタンは管理者または撮影主催者のみ使用できます。", ephemeral=True)
            return

        # ロールを取得
        role = interaction.guild.get_role(self.role_id)
        if not role:
            await interaction.response.send_message("撮影ロールが見つかりませんでした。", ephemeral=True)
            return
        
        # 全参加者からロールを削除
        removed_count = 0
        for user_id in self.participants:
            member = interaction.guild.get_member(user_id)
            if member and role in member.roles:
                try:
                    await member.remove_roles(role, reason="撮影終了")
                    removed_count += 1
                except:
                    pass
        
        # 通知チャンネルに終了メッセージを送信
        try:
            announcement_channel = interaction.guild.get_channel(ANNOUNCEMENT_CHANNEL_ID)
            if announcement_channel:
                await announcement_channel.send(f"**撮影が終了しました。** （ロール解除: {removed_count}人）")
            
            participants_channel = interaction.guild.get_channel(PARTICIPANTS_CHANNEL_ID)
            if participants_channel:
                await participants_channel.send("**撮影が終了しました。** 皆様お疲れ様でした。")
        except Exception as e:
            print(f"撮影終了通知の送信中にエラーが発生しました: {e}")
        
        # ボタンを無効化
        self.disabled = True
        self.label = "撮影は終了しました"
        for child in self.view.children:
            child.disabled = True
        
        await interaction.response.edit_message(view=self.view)
        await interaction.followup.send(f"撮影を終了しました。参加者 {removed_count}人 からロールを削除しました。", ephemeral=True)

class CancelParticipationButton(Button):
    """撮影を辞退するボタン"""
    def __init__(self, role_id: int, participants: List[int]):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label="撮影を辞退する",
            custom_id="cancel_participation"
        )
        self.role_id = role_id
        self.participants = participants
    
    async def callback(self, interaction: discord.Interaction):
        # ロールを取得
        role = interaction.guild.get_role(self.role_id)
        if not role:
            await interaction.response.send_message("撮影ロールが見つかりませんでした。", ephemeral=True)
            return
        
        # 参加者からユーザーを削除
        if interaction.user.id in self.participants:
            self.participants.remove(interaction.user.id)
        
        # ユーザーからロールを削除
        if role in interaction.user.roles:
            try:
                await interaction.user.remove_roles(role, reason="撮影辞退")
                await interaction.response.send_message("撮影を辞退しました。参加ロールを削除しました。", ephemeral=True)
            except:
                await interaction.response.send_message("ロールの削除中にエラーが発生しました。", ephemeral=True)
        else:
            await interaction.response.send_message("撮影に参加していません。", ephemeral=True)

class JoinSatueiButton(Button):
    """撮影に参加するボタン"""
    def __init__(self, role_id: int, participants: List[int], max_participants: Optional[int] = None):
        super().__init__(
            style=discord.ButtonStyle.primary,
            label="撮影に参加する",
            custom_id="join_satuei"
        )
        self.role_id = role_id
        self.participants = participants
        self.max_participants = max_participants
    
    async def callback(self, interaction: discord.Interaction):
        # 参加人数を確認
        if self.max_participants and len(self.participants) >= self.max_participants:
            # すでに参加者リストに含まれている場合は許可
            if interaction.user.id not in self.participants:
                await interaction.response.send_message(
                    f"参加人数が上限（{self.max_participants}人）に達しています。", 
                    ephemeral=True
                )
                return
        
        # ロールを取得
        role = interaction.guild.get_role(self.role_id)
        if not role:
            await interaction.response.send_message("撮影ロールが見つかりませんでした。", ephemeral=True)
            return
        
        # すでに参加している場合
        if interaction.user.id in self.participants:
            await interaction.response.send_message("すでに撮影に参加しています。", ephemeral=True)
            return
        
        # 参加者リストに追加
        self.participants.append(interaction.user.id)
        
        # ユーザーにロールを付与
        try:
            await interaction.user.add_roles(role, reason="撮影参加")
            
            # 参加状況を表示
            participants_info = f"参加者数: {len(self.participants)}"
            if self.max_participants:
                participants_info += f" / {self.max_participants}"
            
            await interaction.response.send_message(
                f"撮影に参加しました！{participants_info}\n"
                "参加者向けチャンネルをご確認ください。", 
                ephemeral=True
            )
        except Exception as e:
            print(f"ロール付与中にエラーが発生: {e}")
            await interaction.response.send_message("ロールの付与中にエラーが発生しました。", ephemeral=True)

class SatueiView(View):
    """撮影参加ビュー"""
    def __init__(self, role_id: int, max_participants: Optional[int] = None, owner_id: int = None):
        super().__init__(timeout=None)  # タイムアウトなし
        self.role_id = role_id
        self.participants = []
        self.max_participants = max_participants
        self.owner_id = owner_id
        
        # 参加ボタンを追加
        self.add_item(JoinSatueiButton(role_id, self.participants, max_participants))

class SatueiCommands(app_commands.Group):
    """撮影コマンドを管理するクラス"""
    
    def __init__(self):
        super().__init__(name="satuei", description="撮影関連のコマンド")
    
    @app_commands.command(name="satuei", description="撮影参加者を募集します")
    @app_commands.describe(
        role="参加者に付与するロール",
        title="撮影タイトル",
        description="撮影の詳細説明",
        max_participants="最大参加人数（未設定の場合は無制限）",
    )
    async def satuei(
        self, 
        interaction: discord.Interaction, 
        role: discord.Role,
        title: str,
        description: Optional[str] = None,
        max_participants: Optional[int] = None
    ):
        """撮影参加者を募集し、チャンネルに通知を送信します"""
        # 権限チェック
        if not interaction.user.guild_permissions.administrator and not any(r.name == "BOT操作" for r in interaction.user.roles):
            await interaction.response.send_message("このコマンドを使用するには管理者権限または「BOT操作」ロールが必要です。", ephemeral=True)
            return
        
        # 現在の日時を取得
        now = datetime.datetime.now()
        date_str = now.strftime("%m月%d日%H時%M分")
        
        # 募集用の埋め込みメッセージを作成
        embed = discord.Embed(
            title=f"📷 {title}",
            description=description or "撮影参加者を募集しています！",
            color=discord.Color.blue()
        )
        embed.add_field(name="主催者", value=interaction.user.mention, inline=True)
        embed.add_field(name="日時", value=date_str, inline=True)
        embed.add_field(name="参加ロール", value=role.mention, inline=True)
        
        if max_participants:
            embed.add_field(name="募集人数", value=f"{max_participants}人", inline=True)
        else:
            embed.add_field(name="募集人数", value="無制限", inline=True)
        
        # 参加ビューを作成
        view = SatueiView(role.id, max_participants, interaction.user.id)
        
        # コマンドの実行元チャンネルに募集メッセージを送信
        await interaction.response.send_message(embed=embed, view=view)
        
        # 指定されたチャンネルに通知を送信
        try:
            # 撮影開始・終了用チャンネルに通知
            announcement_channel = interaction.guild.get_channel(ANNOUNCEMENT_CHANNEL_ID)
            if announcement_channel:
                # 撮影終了ボタン付きのメッセージを送信
                announcement_embed = discord.Embed(
                    title=f"📷 撮影開始: {title}",
                    description=f"{date_str} 撮影開始",
                    color=discord.Color.green()
                )
                announcement_embed.add_field(name="主催者", value=interaction.user.mention, inline=True)
                
                # 終了ボタン付きのビューを作成
                end_view = View(timeout=None)
                end_view.add_item(EndSatueiButton(role.id, view.participants))
                end_view.owner_id = interaction.user.id
                
                await announcement_channel.send(embed=announcement_embed, view=end_view)
            
            # 参加者向けチャンネルに通知
            participants_channel = interaction.guild.get_channel(PARTICIPANTS_CHANNEL_ID)
            if participants_channel:
                # 辞退ボタン付きのメッセージを送信
                participants_embed = discord.Embed(
                    title=f"📷 撮影開始: {title}",
                    description=f"{date_str} 撮影開始\n\n{description or ''}",
                    color=discord.Color.blue()
                )
                participants_embed.add_field(name="主催者", value=interaction.user.mention, inline=True)
                
                # 辞退ボタン付きのビューを作成
                cancel_view = View(timeout=None)
                cancel_view.add_item(CancelParticipationButton(role.id, view.participants))
                
                await participants_channel.send(embed=participants_embed, view=cancel_view)
            
        except Exception as e:
            print(f"通知の送信中にエラーが発生しました: {e}")
            await interaction.followup.send("通知の送信中にエラーが発生しました。", ephemeral=True)
