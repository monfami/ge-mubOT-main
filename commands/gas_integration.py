import discord
import json
import os
from datetime import datetime
from discord.ui import Button, View

# 認証システムのクラス
class AuthSystem:
    def __init__(self):
        self.members_file = "mennba.json"
        self._load_members()
    
    def _load_members(self):
        """メンバー情報をJSONファイルから読み込む"""
        if os.path.exists(self.members_file):
            try:
                with open(self.members_file, 'r', encoding='utf-8') as f:
                    self.members = json.load(f)
            except json.JSONDecodeError:
                self.members = {}
        else:
            self.members = {}
    
    def _save_members(self):
        """メンバー情報をJSONファイルに保存する"""
        with open(self.members_file, 'w', encoding='utf-8') as f:
            json.dump(self.members, f, ensure_ascii=False, indent=4)
    
    def register_member(self, user):
        """ユーザー情報を登録する"""
        user_id = str(user.id)  # JSONのキーは文字列である必要がある
        
        # ユーザー情報を記録
        self.members[user_id] = {
            "username": user.name,
            "user_id": user.id,
            "registration_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "profile": {
                "display_name": user.display_name,
                "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "avatar_url": str(user.avatar.url) if user.avatar else None
            }
        }
        
        # 変更を保存
        self._save_members()
        return True
    
    def is_registered(self, user_id):
        """ユーザーが登録済みかどうかを確認する"""
        return str(user_id) in self.members

# 認証ボタンのView
class AuthView(View):
    def __init__(self, auth_system, role_id):
        super().__init__(timeout=None)  # タイムアウトなし
        self.auth_system = auth_system
        self.role_id = role_id
    
    @discord.ui.button(label="認証する", style=discord.ButtonStyle.green, custom_id="authenticate")
    async def authenticate_button(self, interaction: discord.Interaction, button: Button):
        user = interaction.user
        
        # すでに認証済みの場合
        if self.auth_system.is_registered(user.id):
            await interaction.response.send_message("あなたはすでに認証済みです。", ephemeral=True)
            return
        
        # 認証処理
        success = self.auth_system.register_member(user)
        
        if success:
            # ロールを付与
            try:
                role = interaction.guild.get_role(self.role_id)
                if role:
                    await user.add_roles(role)
                    await interaction.response.send_message(
                        f"認証が完了しました！{role.mention}ロールが付与されました。", 
                        ephemeral=True
                    )
                else:
                    await interaction.response.send_message(
                        "認証は完了しましたが、ロールの付与に失敗しました。管理者に連絡してください。", 
                        ephemeral=True
                    )
            except Exception as e:
                await interaction.response.send_message(
                    f"認証は完了しましたが、エラーが発生しました: {str(e)}", 
                    ephemeral=True
                )
        else:
            await interaction.response.send_message("認証に失敗しました。再試行してください。", ephemeral=True)
