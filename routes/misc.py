from flask import Blueprint, jsonify, send_file, send_from_directory, request
import os
from telethon import TelegramClient
from urllib.parse import urlparse
import asyncio

misc_bp = Blueprint("misc", __name__)

api_id = 29797888
api_hash = '3a8c11f2cd481c12f4184eddf560395f'

# ✅ Endpoint GET mặc định để show tên chủ API
@misc_bp.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Welcome to Telegram API by huydev 🚀"}), 200

# ✅ Hàm phân tích link telegram
def parse_telegram_link(link):
    parsed = urlparse(link)
    parts = parsed.path.strip('/').split('/')
    if len(parts) == 2:
        return parts[0], int(parts[1])
    raise ValueError("❌ Link không hợp lệ. Phải là https://t.me/username/message_id")

# ✅ API lấy bài viết Telegram
@misc_bp.route('/api/get_post', methods=['POST'])
def get_post():
    data = request.json
    link = data.get('link')

    try:
        username, msg_id = parse_telegram_link(link)

        async def run():
            async with TelegramClient('session_api', api_id, api_hash) as client:
                entity = await client.get_entity(username)
                message = await client.get_messages(entity, ids=msg_id)
                if not message:
                    return {"error": "Không tìm thấy bài viết"}, 404

                vietnam_tz = timezone("Asia/Ho_Chi_Minh")
                local_date = message.date.astimezone(vietnam_tz)
                return {
                    "id": message.id,
                    "date": local_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "views": message.views,
                    "comments": message.replies.replies if message.replies else 0,
                    "text": message.text,
                    "has_media": bool(message.media),
                    "reactions": [
                        {
                            "emoji": getattr(r.reaction, "emoticon", str(r.reaction)),
                            "count": r.count
                        }
                        for r in message.reactions.results
                    ] if message.reactions else []
                }

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        result = loop.run_until_complete(run())
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@misc_bp.route('/api/get_gemini_keys', methods=['GET'])
def get_gemini_keys():
    try:
        file_path = 'gemini_key.txt'  # 👉 Boss đổi tên file nếu cần

        if not os.path.exists(file_path):
            return jsonify({"error": "Không tìm thấy file gemini_key.txt"}), 404

        with open(file_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]

        return jsonify({
            "total_keys": len(lines),
            "keys": lines
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@misc_bp.route('/api/checker_key', methods=['GET'])
def get_clone_voice_keys():
    try:
        file_path = 'clone_voice_key.txt'  # 👉 Boss đổi tên file nếu cần

        if not os.path.exists(file_path):
            return jsonify({"error": "Không tìm thấy file clone_voice_key.txt"}), 404

        with open(file_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]

        return jsonify({
            "total_keys": len(lines),
            "keys": lines
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@misc_bp.route("/api/get_gemini_languages", methods=["GET"])
def get_gemini_languages():
    return jsonify({
        "languages": [
            {"name": "Vietnam", "code": "vi"},
            {"name": "English", "code": "en"},
            {"name": "Spanish", "code": "es"},
            {"name": "French", "code": "fr"},
            {"name": "German", "code": "de"},
            {"name": "Italian", "code": "it"},
            {"name": "Portuguese", "code": "pt"},
            {"name": "Dutch", "code": "nl"},
            {"name": "Russian", "code": "ru"},
            {"name": "Polish", "code": "pl"},
            {"name": "Ukrainian", "code": "uk"},
            {"name": "Chinese (Simplified)", "code": "zh"},
            {"name": "Chinese (Traditional)", "code": "zh-TW"},
            {"name": "Japanese", "code": "ja"},
            {"name": "Korean", "code": "ko"},
            {"name": "Arabic", "code": "ar"},
            {"name": "Hindi", "code": "hi"},
            {"name": "Bengali", "code": "bn"},
            {"name": "Turkish", "code": "tr"},
            {"name": "Greek", "code": "el"},
            {"name": "Czech", "code": "cs"},
            {"name": "Romanian", "code": "ro"},
            {"name": "Hungarian", "code": "hu"},
            {"name": "Finnish", "code": "fi"},
            {"name": "Swedish", "code": "sv"},
            {"name": "Danish", "code": "da"},
            {"name": "Norwegian", "code": "no"},
            {"name": "Thai", "code": "th"},
            {"name": "Vietnamese", "code": "vi"},
            {"name": "Indonesian", "code": "id"},
            {"name": "Malay", "code": "ms"},
            {"name": "Tamil", "code": "ta"},
            {"name": "Telugu", "code": "te"},
            {"name": "Marathi", "code": "mr"},
            {"name": "Punjabi", "code": "pa"},
            {"name": "Gujarati", "code": "gu"},
            {"name": "Burmese", "code": "my"},
            {"name": "Filipino (Tagalog)", "code": "tl"},
            {"name": "Urdu", "code": "ur"},
            {"name": "Persian", "code": "fa"},
            {"name": "Hebrew", "code": "he"},
            {"name": "Swahili", "code": "sw"},
            {"name": "Catalan", "code": "ca"},
            {"name": "Basque", "code": "eu"},
            {"name": "Serbian", "code": "sr"},
            {"name": "Croatian", "code": "hr"},
            {"name": "Slovak", "code": "sk"},
            {"name": "Slovenian", "code": "sl"},
            {"name": "Bulgarian", "code": "bg"},
            {"name": "Lithuanian", "code": "lt"},
            {"name": "Latvian", "code": "lv"},
            {"name": "Estonian", "code": "et"},
            {"name": "Macedonian", "code": "mk"},
            {"name": "Albanian", "code": "sq"},
            {"name": "Belarusian", "code": "be"},
            {"name": "Icelandic", "code": "is"},
            {"name": "Georgian", "code": "ka"},
            {"name": "Armenian", "code": "hy"},
            {"name": "Malayalam", "code": "ml"},
            {"name": "Sinhalese", "code": "si"},
            {"name": "Khmer", "code": "km"},
            {"name": "Lao", "code": "lo"},
            {"name": "Mongolian", "code": "mn"},
            {"name": "Tajik", "code": "tg"},
            {"name": "Pashto", "code": "ps"},
            {"name": "Amharic", "code": "am"},
            {"name": "Haitian Creole", "code": "ht"},
            {"name": "Yoruba", "code": "yo"},
            {"name": "Igbo", "code": "ig"},
            {"name": "Zulu", "code": "zu"},
            {"name": "Quechua", "code": "qu"},
            {"name": "Azerbaijani", "code": "az"},
            {"name": "Uzbek", "code": "uz"},
            {"name": "Kazakh", "code": "kk"},
            {"name": "Hmong", "code": "hmn"},
            {"name": "Somali", "code": "so"},
            {"name": "Nepali", "code": "ne"},
            {"name": "Tigrinya", "code": "ti"}
        ]
    })



@misc_bp.route('/api/version.json')
def get_version():
    return send_file('version.json', mimetype='application/json')

@misc_bp.route('/downloads/<filename>')
def download_file(filename):
    download_folder = os.path.join(os.getcwd(), 'downloads')
    return send_from_directory(directory=download_folder, path=filename, as_attachment=True)


UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
@misc_bp.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "Không tìm thấy file trong request"}), 400
    
    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "Tên file không được để trống"}), 400

    save_path = os.path.join(UPLOAD_FOLDER, file.filename)
    try:
        file.save(save_path)
        return jsonify({"message": f"Upload thành công file: {file.filename}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500