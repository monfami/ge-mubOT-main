from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

# 認証データを保存するファイル
VERIFICATION_DATA_FILE = 'verification_data.json'

# 認証データをロード
if os.path.exists(VERIFICATION_DATA_FILE):
    with open(VERIFICATION_DATA_FILE, 'r', encoding='utf-8') as f:
        verification_data = json.load(f)
else:
    verification_data = {}

@app.route('/verify/<verification_id>', methods=['GET'])
def verify(verification_id):
    """認証処理を行うエンドポイント"""
    if verification_id not in verification_data:
        return jsonify({"error": "Invalid verification ID"}), 404

    # 認証データを取得
    data = verification_data.pop(verification_id)
    user_id = data["user_id"]
    role_id = data["role_id"]
    guild_id = data["guild_id"]

    # 認証成功のレスポンス
    with open(VERIFICATION_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(verification_data, f, ensure_ascii=False, indent=4)

    return jsonify({
        "message": "Verification successful!",
        "user_id": user_id,
        "role_id": role_id,
        "guild_id": guild_id
    })

@app.route('/add_verification', methods=['POST'])
def add_verification():
    """認証データを追加するエンドポイント"""
    data = request.json
    verification_id = data.get("verification_id")
    user_id = data.get("user_id")
    role_id = data.get("role_id")
    guild_id = data.get("guild_id")

    if not all([verification_id, user_id, role_id, guild_id]):
        return jsonify({"error": "Missing required fields"}), 400

    verification_data[verification_id] = {
        "user_id": user_id,
        "role_id": role_id,
        "guild_id": guild_id
    }

    with open(VERIFICATION_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(verification_data, f, ensure_ascii=False, indent=4)

    return jsonify({"message": "Verification data added successfully!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
