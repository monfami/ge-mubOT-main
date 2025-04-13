import discord
import os
from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv()

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
        bot_role_name = os.getenv("BOT_ROLE_NAME", "BOT!")
        bot_role = discord.utils.get(guild.roles, name=bot_role_name)
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
        
        # 管理者用のビューと参加者用のビューはそれぞれのビュークラスからインポートされるので
        # この段階ではインポートしていない。それらはbot.pyで組み合わせる
        
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
                
                view = discord.ui.View()
                button = discord.ui.Button(label="募集は終了しました", style=discord.ButtonStyle.secondary, disabled=True)
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
                
                view = discord.ui.View()
                button = discord.ui.Button(label="募集は終了しました", style=discord.ButtonStyle.secondary, disabled=True)
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
        has_admin_role = discord.utils.get(user.roles, name=os.getenv("ADMIN_ROLE_NAME", "BOT操作")) is not None
        is_host = user.id == recruitment["host"]
        
        return is_host or has_admin_role
