import discord
from discord import ui
from commands.game_recruitment import GameRecruitment

# 公開募集用のボタンビュー
class PublicJoinView(ui.View):
    def __init__(self, recruitment_id):
        super().__init__(timeout=None)
        self.recruitment_id = recruitment_id
    
    @ui.button(label="参加する", style=discord.ButtonStyle.primary, custom_id="public_join_game")
    async def join_button(self, interaction: discord.Interaction, button: ui.Button):
        success, result = await GameRecruitment.add_player(interaction, self.recruitment_id)
        
        if success:
            recruitment = GameRecruitment.recruitments.get(self.recruitment_id)
            if recruitment:
                if result["is_full"]:
                    # 募集が満員になった場合
                    button.disabled = True
                    button.label = "募集は終了しました"
                    button.style = discord.ButtonStyle.secondary
                    
                    embed = interaction.message.embeds[0]
                    embed.color = discord.Color.light_grey()
                    # 正しい参加人数を表示
                    embed.description = embed.description.split('\n\n')[0] + f"\n\n参加人数: {result['current_players']}/{result['max_players']}"
                    embed.set_footer(text="この募集は終了しました")
                    await interaction.message.edit(embed=embed, view=self)
                
                else:
                    # 埋め込みメッセージの更新
                    embed = interaction.message.embeds[0]
                    # 正しい参加人数を表示
                    embed.description = embed.description.split('\n\n')[0] + f"\n\n参加人数: {result['current_players']}/{result['max_players']}"
                    await interaction.message.edit(embed=embed)
                
                # プライベートチャンネルの埋め込みメッセージも更新
                try:
                    text_channel = interaction.guild.get_channel(recruitment["text_channel"])
                    async for message in text_channel.history(limit=10):
                        if message.author == interaction.client.user and message.embeds and len(message.embeds) > 0:
                            embed = message.embeds[0]
                            if embed.title == f"{recruitment['game_type']}の募集":
                                # プライベートチャンネルの埋め込みメッセージを更新
                                new_embed = discord.Embed(
                                    title=embed.title,
                                    description=f"ホスト: {interaction.guild.get_member(recruitment['host']).mention}\n"
                                              f"参加人数: {result['current_players']}/{result['max_players']}",
                                    color=embed.color
                                )
                                if embed.footer.text:
                                    new_embed.set_footer(text=embed.footer.text)
                                await message.edit(embed=new_embed)
                                break
                except Exception as e:
                    print(f"プライベートチャンネルの更新でエラー発生: {e}")
                
                # テキストチャンネルとボイスチャンネルのリンクを送信
                text_channel = interaction.guild.get_channel(recruitment["text_channel"])
                voice_channel = interaction.guild.get_channel(recruitment["voice_channel"])
                
                # チャンネル情報と共に管理ボタンを表示（権限がある場合のみ）
                if GameRecruitment.has_management_permission(interaction.user, self.recruitment_id):
                    from views.management_view import GameManagementView
                    management_view = GameManagementView(self.recruitment_id, result["max_players"])
                    await interaction.response.send_message(
                        f"{interaction.user.mention}が参加しました！\n"
                        f"テキストチャンネル: {text_channel.mention}\n"
                        f"ボイスチャンネル: {voice_channel.mention}\n"
                        f"※あなたは管理権限を持っています。下のボタンから募集を管理できます。", 
                        view=management_view,
                        ephemeral=True
                    )
                else:
                    await interaction.response.send_message(
                        f"{interaction.user.mention}が参加しました！\n"
                        f"テキストチャンネル: {text_channel.mention}\n"
                        f"ボイスチャンネル: {voice_channel.mention}", 
                        ephemeral=True
                    )
            else:
                await interaction.response.send_message("エラーが発生しました。", ephemeral=True)
        else:
            await interaction.response.send_message(result, ephemeral=True)
