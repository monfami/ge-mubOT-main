import discord
from discord import ui
from game_recruitment import GameRecruitment

# 一般参加者用ビュー（退出ボタン付き）
class GameMemberView(ui.View):
    def __init__(self, recruitment_id):
        super().__init__(timeout=None)
        self.recruitment_id = recruitment_id
    
    @ui.button(label="募集から抜ける", style=discord.ButtonStyle.secondary, emoji="👋")
    async def leave_button(self, interaction: discord.Interaction, button: ui.Button):
        success, result = await GameRecruitment.remove_player(interaction, self.recruitment_id)
        
        if success:
            await interaction.response.send_message(result, ephemeral=True)
        else:
            await interaction.response.send_message(result, ephemeral=True)
