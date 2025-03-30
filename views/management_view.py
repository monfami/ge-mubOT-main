import discord
from discord import ui
from game_recruitment import GameRecruitment

# ゲーム管理用ビュー (ホスト・管理者用)
class GameManagementView(ui.View):
    def __init__(self, recruitment_id, max_players):
        super().__init__(timeout=None)
        self.recruitment_id = recruitment_id
        self.max_players = max_players

    @ui.button(label="募集を締め切る", style=discord.ButtonStyle.danger, row=0)
    async def close_button(self, interaction: discord.Interaction, button: ui.Button):
        # 権限チェック
        if not GameRecruitment.has_management_permission(interaction.user, self.recruitment_id):
            await interaction.response.send_message("この操作を行う権限がありません。募集作成者または@BOT操作ロールを持つメンバーのみが可能です。", ephemeral=True)
            return
            
        success, result = await GameRecruitment.close_recruitment(interaction, self.recruitment_id)
        
        if success:
            # ボタン更新
            for child in self.children:
                if child.label == "募集を締め切る":
                    child.disabled = True
                    child.label = "募集締め切り済み"
                    child.style = discord.ButtonStyle.secondary
                
            embed = interaction.message.embeds[0]
            embed.color = discord.Color.light_grey()
            embed.set_footer(text="この募集は終了しました")
            
            await interaction.message.edit(embed=embed, view=self)
            await interaction.response.send_message("募集を終了しました", ephemeral=True)
        else:
            await interaction.response.send_message(result, ephemeral=True)

    @ui.button(label="ゲームを終了する", style=discord.ButtonStyle.red, row=0)
    async def delete_button(self, interaction: discord.Interaction, button: ui.Button):
        # 権限チェック
        if not GameRecruitment.has_management_permission(interaction.user, self.recruitment_id):
            await interaction.response.send_message("この操作を行う権限がありません。募集作成者または@BOT操作ロールを持つメンバーのみが可能です。", ephemeral=True)
            return
            
        # 確認ダイアログを表示
        from views.confirm_view import ConfirmDeleteView
        confirm_view = ConfirmDeleteView(self.recruitment_id)
        await interaction.response.send_message(
            "**⚠️警告: この操作は取り消せません**\n"
            "ゲームチャンネルを削除しますか？このアクションはすぐに実行され、チャットの履歴はすべて失われます。",
            view=confirm_view,
            ephemeral=True
        )
