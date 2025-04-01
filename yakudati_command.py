import discord
from discord import app_commands
import random
import re

def setup_yakudati_commands(bot):
    """役立ちメンバーコマンドをセットアップする関数"""
    
    @bot.tree.command(
        name="yakudati",
        description="指定した月の役立ちメンバーランキングを表示します"
    )
    @app_commands.describe(
        month="表示する月（例: 4、5月など）",
        member1="1位のメンバー名（ユーザー名またはID）",
        member2="2位のメンバー名（ユーザー名またはID）",
        member3="3位のメンバー名（ユーザー名またはID）"
    )
    async def yakudati_command(
        interaction: discord.Interaction, 
        month: str,
        member1: str,
        member2: str,
        member3: str
    ):
        """役立ちメンバーランキングを表示するコマンド"""
        
        # 実行者の名前を取得
        user_name = interaction.user.name
        
        # メンバーを検索する関数
        async def find_members(member_input):
            result = []
            parts = member_input.split()
            
            for part in parts:
                # IDパターンを検出
                id_match = re.search(r'(\d+)', part)
                if id_match:
                    user_id = id_match.group(1)
                    try:
                        # IDからメンバーを検索
                        user = await interaction.guild.fetch_member(int(user_id))
                        if user:
                            # 実際のメンションを使用（青色になる）
                            result.append(user.mention)
                            continue
                    except:
                        pass
                
                # 名前でメンバーを検索
                cleaned_name = part.replace('@', '')
                found = False
                
                for member in interaction.guild.members:
                    # ユーザー名、表示名のいずれかと一致するか確認
                    if (cleaned_name.lower() == member.name.lower() or 
                        cleaned_name.lower() == member.display_name.lower()):
                        # 実際のメンションを使用（青色になる）
                        result.append(member.mention)
                        found = True
                        break
                
                # サーバー内に見つからない場合は@付きテキストで表示
                if not found:
                    result.append(f"@{cleaned_name}")
            
            return " ".join(result)
        
        # 各メンバー名を解決
        member1_formatted = await find_members(member1)
        member2_formatted = await find_members(member2)
        member3_formatted = await find_members(member3)
            
        # 埋め込みメッセージを作成
        embed = discord.Embed(
            title=f"🏆{month}月の役立ちメンバー🏆",
            description=f"{user_name}からのレポート",
            color=discord.Color.gold()
        )
        
        # 各順位の役立ちメンバーを追加
        embed.add_field(name="🥇第1位", value=member1_formatted, inline=False)
        embed.add_field(name="🥈第2位", value=member2_formatted, inline=False)
        embed.add_field(name="🥉第3位", value=member3_formatted, inline=False)
        
        # フッターを追加
        embed.set_footer(text="来月の授与がんばろう。")
        
        # メッセージを送信
        await interaction.response.send_message(embed=embed)
        
    print("役立ちメンバーコマンドを登録しました")
