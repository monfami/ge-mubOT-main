import discord
from discord.ext import commands
from discord import app_commands, ui
from dotenv import load_dotenv
import os

# .envファイルを読み込む
load_dotenv()

# Intentsを修正してmessage_contentを有効化
intents = discord.Intents.default()
intents.message_content = True

# BOTの設定
bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"), intents=intents)

# ゲームの募集を管理するクラス
class GameRecruitment:
    recruitments = {}  # 募集を保存する辞書

    @classmethod
    async def create_recruitment(cls, interaction, game_type, max_players):
        guild = interaction.guild
        user = interaction.user
        
        # プライベートカテゴリの作成
        category = await guild.create_category(f"{game_type}-{user.display_name}")
        
        # 権限オーバーライドの設定
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, connect=True, speak=True)
        }
        
        # BOT!ロールがある場合は権限を追加
        bot_role = discord.utils.get(guild.roles, name="BOT!")
        if bot_role:
            overwrites[bot_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, connect=True, speak=True)
        
        # テキストチャンネルとボイスチャンネルの作成
        text_channel = await category.create_text_channel(f"{game_type}-チャット", overwrites=overwrites)
        voice_channel = await category.create_voice_channel(f"{game_type}-ボイスチャット", overwrites=overwrites)
        
        # 募集情報を保存
        recruitment_id = str(text_channel.id)
        cls.recruitments[recruitment_id] = {
            "host": user.id,
            "game_type": game_type,
            "max_players": max_players,
            "current_players": [user.id],
            "category": category.id,
            "text_channel": text_channel.id,
            "voice_channel": voice_channel.id,
            "public_message_id": None,
            "public_channel_id": None,
        }
        
        # 参加用ビューを作成（権限に応じて表示を変える）
        game_info_embed = discord.Embed(
            title=f"{game_type}の募集",
            description=f"ホスト: {user.mention}\n"
                       f"参加人数: 1/{max_players}",
            color=discord.Color.blue()
        )
        
        # 管理者用のビュー
        host_view = GameManagementView(recruitment_id, max_players)
        await text_channel.send(embed=game_info_embed, view=host_view)
        
        # 参加者用のビュー（退出ボタン付き）
        member_view = GameMemberView(recruitment_id)
        await text_channel.send(
            f"**ようこそ {game_type} の募集チャンネルへ！**\n\n"
            f"このチャンネルはゲームの参加者専用です。\n"
            f"ボイスチャットはこちら: {voice_channel.mention}\n\n"
            f"ゲームが終了したら、ホストまたは管理者が「ゲームを終了する」ボタンを押すことでチャンネルを削除できます。", 
            view=member_view
        )
        
        return text_channel, voice_channel, category, recruitment_id

    @classmethod
    async def add_player(cls, interaction, recruitment_id):
        recruitment = cls.recruitments.get(recruitment_id)
        if not recruitment:
            return False, "募集が見つかりません"
        
        user_id = interaction.user.id
        if user_id in recruitment["current_players"]:
            return False, "あなたはすでに参加しています"
            
        if len(recruitment["current_players"]) >= recruitment["max_players"]:
            return False, "募集が満員です"
            
        # メンバーを追加
        recruitment["current_players"].append(user_id)
        
        # チャンネルのアクセス権を付与
        guild = interaction.guild
        user = interaction.user
        category = guild.get_channel(recruitment["category"])
        text_channel = guild.get_channel(recruitment["text_channel"])
        voice_channel = guild.get_channel(recruitment["voice_channel"])
        
        # テキストチャンネルとボイスチャンネルの両方に明示的に権限を付与
        await text_channel.set_permissions(user, read_messages=True, send_messages=True)
        await voice_channel.set_permissions(user, connect=True, speak=True, view_channel=True)
        
        # 募集が満員になったか確認
        is_full = len(recruitment["current_players"]) >= recruitment["max_players"]
        
        # 参加したことをテキストチャンネルに通知
        try:
            host = guild.get_member(recruitment["host"])
            host_mention = host.mention if host else "ホスト"
            await text_channel.send(f"🎉 {user.mention} が参加しました！ ({len(recruitment['current_players'])}/{recruitment['max_players']}人)")
        except:
            pass
            
        return True, {
            "is_full": is_full,
            "current_players": len(recruitment["current_players"]),
            "max_players": recruitment["max_players"]
        }

    @classmethod
    async def remove_player(cls, interaction, recruitment_id):
        """プレイヤーを募集から削除する"""
        recruitment = cls.recruitments.get(recruitment_id)
        if not recruitment:
            return False, "募集が見つかりません"
        
        user_id = interaction.user.id
        
        # ホストは退出できない
        if user_id == recruitment["host"]:
            return False, "あなたはホストなので退出できません。ゲームを終了するには「ゲームを終了する」ボタンを使用してください。"
        
        # 参加者リストに含まれているか確認
        if user_id not in recruitment["current_players"]:
            return False, "あなたはこの募集に参加していません"
        
        # プレイヤーを削除
        recruitment["current_players"].remove(user_id)
        
        # チャンネルのアクセス権を削除
        guild = interaction.guild
        user = interaction.user
        text_channel = guild.get_channel(recruitment["text_channel"])
        voice_channel = guild.get_channel(recruitment["voice_channel"])
        
        if text_channel:
            await text_channel.set_permissions(user, overwrite=None)
        if voice_channel:
            await voice_channel.set_permissions(user, overwrite=None)
            
        # 退出したことを通知
        try:
            await text_channel.send(f"👋 {user.mention} が退出しました。(現在の参加人数: {len(recruitment['current_players'])}/{recruitment['max_players']})")
        except:
            pass
            
        # プライベートチャンネルの埋め込みメッセージを更新
        try:
            async for message in text_channel.history(limit=20):
                if message.author == interaction.client.user and message.embeds and len(message.embeds) > 0:
                    embed = message.embeds[0]
                    if embed.title == f"{recruitment['game_type']}の募集":
                        # 埋め込みメッセージを更新
                        new_embed = discord.Embed(
                            title=embed.title,
                            description=f"ホスト: {interaction.guild.get_member(recruitment['host']).mention}\n"
                                      f"参加人数: {len(recruitment['current_players'])}/{recruitment['max_players']}",
                            color=embed.color
                        )
                        if embed.footer.text:
                            new_embed.set_footer(text=embed.footer.text)
                        await message.edit(embed=new_embed)
                        break
        except Exception as e:
            print(f"プライベートチャンネルの更新でエラー発生: {e}")
            
        # 公開メッセージも更新
        try:
            if recruitment["public_message_id"] and recruitment["public_channel_id"]:
                channel = guild.get_channel(recruitment["public_channel_id"])
                message = await channel.fetch_message(recruitment["public_message_id"])
                
                embed = message.embeds[0]
                embed.description = embed.description.split('\n\n')[0] + f"\n\n参加人数: {len(recruitment['current_players'])}/{recruitment['max_players']}"
                await message.edit(embed=embed)
        except:
            pass
            
        return True, f"{recruitment['game_type']}の募集から退出しました。"

    @classmethod
    async def close_recruitment(cls, interaction, recruitment_id):
        recruitment = cls.recruitments.get(recruitment_id)
        if not recruitment:
            return False, "募集が見つかりません"
        
        # 募集を閉じる権限チェック
        user = interaction.user
        has_admin_role = discord.utils.get(user.roles, name="BOT操作") is not None
        is_host = user.id == recruitment["host"]
        
        if not (is_host or has_admin_role):
            return False, "募集を閉じる権限がありません。募集作成者または@BOT操作ロールを持つメンバーのみが可能です。"
        
        # 募集を閉じたことを全員に通知
        guild = interaction.guild
        if recruitment["public_message_id"] and recruitment["public_channel_id"]:
            try:
                channel = guild.get_channel(recruitment["public_channel_id"])
                message = await channel.fetch_message(recruitment["public_message_id"])
                
                # ボタンを無効化して更新
                embed = message.embeds[0]
                embed.color = discord.Color.light_grey()
                embed.set_footer(text="この募集は終了しました")
                
                view = ui.View()
                button = ui.Button(label="募集は終了しました", style=discord.ButtonStyle.secondary, disabled=True)
                view.add_item(button)
                
                await message.edit(embed=embed, view=view)
            except:
                pass
        
        return True, "募集を終了しました"

    @classmethod
    async def delete_channels(cls, interaction, recruitment_id):
        recruitment = cls.recruitments.get(recruitment_id)
        if not recruitment:
            return False, "ゲームチャンネルが見つかりません"

        # 削除権限チェック
        user = interaction.user
        has_admin_role = discord.utils.get(user.roles, name="BOT操作") is not None
        is_host = user.id == recruitment["host"]
        
        if not (is_host or has_admin_role):
            return False, "チャンネルを削除する権限がありません。募集作成者または@BOT操作ロールを持つメンバーのみが可能です。"

        # 公開メッセージを「募集は終了しました」に更新
        guild = interaction.guild
        if recruitment["public_message_id"] and recruitment["public_channel_id"]:
            try:
                channel = guild.get_channel(recruitment["public_channel_id"])
                message = await channel.fetch_message(recruitment["public_message_id"])
                
                # ボタンを無効化して更新
                embed = message.embeds[0]
                embed.color = discord.Color.light_grey()
                embed.set_footer(text="この募集は終了しました (チャンネル削除済み)")
                
                view = ui.View()
                button = ui.Button(label="募集は終了しました", style=discord.ButtonStyle.secondary, disabled=True)
                view.add_item(button)
                
                await message.edit(embed=embed, view=view)
            except:
                pass

        # チャンネル削除処理
        try:
            # カテゴリ、テキスト、ボイスチャンネルの取得
            category = guild.get_channel(recruitment["category"])
            text_channel = guild.get_channel(recruitment["text_channel"])
            voice_channel = guild.get_channel(recruitment["voice_channel"])
            
            # チャンネルの削除
            if text_channel:
                await text_channel.delete()
            if voice_channel:
                await voice_channel.delete()
            if category:
                await category.delete()
                
            # 募集情報を削除
            del cls.recruitments[recruitment_id]
            return True, "ゲームチャンネルを削除しました"
        except Exception as e:
            return False, f"チャンネル削除中にエラーが発生しました: {str(e)}"

    @classmethod
    def has_management_permission(cls, user, recruitment_id):
        """ユーザーがゲーム募集を管理する権限を持っているか確認"""
        recruitment = cls.recruitments.get(recruitment_id)
        if not recruitment:
            return False
            
        # ホストまたはBOT操作ロールを持っている場合は権限あり
        has_admin_role = discord.utils.get(user.roles, name="BOT操作") is not None
        is_host = user.id == recruitment["host"]
        
        return is_host or has_admin_role

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
        confirm_view = ConfirmDeleteView(self.recruitment_id)
        await interaction.response.send_message(
            "**⚠️警告: この操作は取り消せません**\n"
            "ゲームチャンネルを削除しますか？このアクションはすぐに実行され、チャットの履歴はすべて失われます。",
            view=confirm_view,
            ephemeral=True
        )

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

# ゲームコマンドグループ
class GameCommands(app_commands.Group):
    def __init__(self):
        super().__init__(name="game", description="ゲーム関連のコマンド")
    
    # 汎用的な募集コマンド
    @app_commands.command(name="recruit", description="ゲームの募集を作成します")
    @app_commands.describe(
        ゲーム名="募集したいゲームの名前",
        人数="募集する最大人数"
    )
    async def recruit(self, interaction: discord.Interaction, ゲーム名: str, 人数: int = 4):
        if 人数 < 2 or 人数 > 16:
            await interaction.response.send_message("募集人数は2人から16人までにしてください。", ephemeral=True)
            return
            
        await interaction.response.defer(ephemeral=True)
        
        # プライベートチャンネルを作成
        text_channel, voice_channel, category, recruitment_id = await GameRecruitment.create_recruitment(
            interaction, ゲーム名, 人数
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

# Hypixel Worldリンク用コマンドを追加
@bot.tree.command(name="hypixel_world", description="Hypixel Worldのリンクを表示します")
async def hypixel_world(interaction: discord.Interaction):
    """Hypixel Worldのリンクを表示します"""
    hypixel_url = "https://drive.google.com/drive/folders/18w1Y27UJJc_MMS8Yy8tgAc6Sv71A0s6M"
    
    embed = discord.Embed(
        title="Hypixel World リンク",
        description=f"Hypixel Worldは[こちら]({hypixel_url})からアクセスできます。",
        color=discord.Color.gold()
    )
    embed.add_field(name="URL", value=hypixel_url)
    embed.set_footer(text="Hypixel World - Minecraft Server Data")
    
    await interaction.response.send_message(embed=embed)

# セットアップコマンド - BOTのスラッシュコマンドとして提供
@bot.tree.command(name="setup", description="BOTの初期設定を行います（管理者のみ）")
@app_commands.default_permissions(administrator=True)
async def setup_command(interaction: discord.Interaction):
    """サーバーに必要なロールを作成します"""
    guild = interaction.guild
    
    # BOT操作ロールの作成
    admin_role_name = "BOT操作"
    existing_admin_role = discord.utils.get(guild.roles, name=admin_role_name)
    
    # BOT!ロールの作成
    bot_role_name = "BOT!"
    existing_bot_role = discord.utils.get(guild.roles, name=bot_role_name)
    
    response = []
    
    if existing_admin_role:
        response.append(f"`{admin_role_name}` ロールはすでに存在します。")
    else:
        try:
            # 目立つ色のロールを作成
            await guild.create_role(name=admin_role_name, colour=discord.Colour.blue(), 
                                   mentionable=True, 
                                   reason="ゲーム募集BOTのセットアップ")
            response.append(f"`{admin_role_name}` ロールを作成しました。このロールを持つユーザーはゲーム募集の管理ができます。")
        except:
            response.append(f"`{admin_role_name}` ロールの作成に失敗しました。BOTに必要な権限があるか確認してください。")
    
    if existing_bot_role:
        response.append(f"`{bot_role_name}` ロールはすでに存在します。")
    else:
        try:
            # BOT!ロールを作成
            await guild.create_role(name=bot_role_name, colour=discord.Colour.purple(), 
                                   mentionable=True, 
                                   reason="BOTの自由参加用ロール")
            response.append(f"`{bot_role_name}` ロールを作成しました。このロールを持つメンバーはすべてのゲームチャンネルに参加できます。")
        except:
            response.append(f"`{bot_role_name}` ロールの作成に失敗しました。BOTに必要な権限があるか確認してください。")
    
    response.append("セットアップが完了しました！`/game recruit` コマンドでゲーム募集を始められます。")
    
    await interaction.response.send_message("\n".join(response))

# スラッシュコマンドの同期
@bot.event
async def on_ready():
    # ゲームコマンドグループを追加
    game_commands = GameCommands()
    bot.tree.add_command(game_commands)
    
    await bot.tree.sync()  # スラッシュコマンドを同期
    print(f"BOTがログインしました: {bot.user}")

# トークンを.envから取得してBOTを起動
bot.run(os.getenv("DISCORD_BOT_TOKEN"))
