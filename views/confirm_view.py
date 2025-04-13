import discord
from discord import ui
from commands.game_recruitment import GameRecruitment

# 削除確認ビュー
class ConfirmDeleteView(ui.View):
    def __init__(self, recruitment_id):
        super().__init__(timeout=60)  # 60秒でタイムアウト
        self.recruitment_id = recruitment_id
    
    @ui.button(label="はい、削除します", style=discord.ButtonStyle.red)
    async def confirm_button(self, interaction: discord.Interaction, button: ui.Button):
        success, result = await GameRecruitment.delete_channels(interaction, self.recruitment_id)
        
        if success:
            for item in self.children:
                item.disabled = True
            await interaction.message.edit(content="チャンネルを削除しました。", view=self)
            await interaction.response.defer()
        else:
            await interaction.response.send_message(result, ephemeral=True)
    
    @ui.button(label="キャンセル", style=discord.ButtonStyle.grey)
    async def cancel_button(self, interaction: discord.Interaction, button: ui.Button):
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(content="チャンネル削除をキャンセルしました。", view=self)
        await interaction.response.defer()
