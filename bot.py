import os
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread
import google.generativeai as genai
from duckduckgo_search import DDGS

# ==========================================
# 1. Web 伺服器保活機制
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "Discord Bot is alive!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    server = Thread(target=run_server)
    server.start()

# ==========================================
# 2. 機器人與 AI 核心設定
# ==========================================
DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

user_chats = {}

@bot.event
async def on_ready():
    print(f"✅ 機器人已成功啟動並登入為 {bot.user}")

# ==========================================
# 3. 全能助理 AI 大腦 (包含網路搜尋)
# ==========================================
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if bot.user.mentioned_in(message):
        user_input = message.content.replace(f'<@{bot.user.id}>', '').strip()

        if not user_input:
            await message.reply("有什麼我可以幫忙的嗎？")
            return

        try:
            async with message.channel.typing():
                
                # 🌐 網路搜尋外掛
                try:
                    search_results = DDGS().text(f"{user_input}", max_results=3)
                    latest_news = "\n".join([f"參考資料: {res['body']}" for res in search_results]) if search_results else "網路上無相關最新資訊。"
                except Exception:
                    latest_news = "網路搜尋暫時無回應，請直接使用你的內建知識庫分析。"

                user_id = message.author.id

                # 🤖 AI 大腦與全能助理人設
                if user_id not in user_chats:
                    system_prompt = (
                        "你現在是一個聰明、友善且無所不知的專屬 AI 助理。"
                        "你可以回答任何領域的問題、協助撰寫程式碼、提供生活建議或進行閒聊。"
                        "請根據用戶的問題提供實用、準確的解答。"
                        "回答請保持排版清晰、易於閱讀，遇到長篇內容請善用條列式或粗體標示重點。"
                    )
                    model = genai.GenerativeModel(
                        model_name='gemini-2.5-flash',
                        system_instruction=system_prompt
                    )
                    user_chats[user_id] = model.start_chat(history=[])

                # 🧠 統整問題並回覆
                combined_prompt = f"【網路參考資訊】\n{latest_news}\n\n【用戶提問】\n{user_input}"
                response = user_chats[user_id].send_message(combined_prompt)
                
                # ✂️ 自動分段，解決字數限制
                reply_text = response.text
                if len(reply_text) > 1900:
                    for i in range(0, len(reply_text), 1900):
                        await message.reply(reply_text[i:i+1900])
                else:
                    await message.reply(reply_text)
                
        except Exception as e:
            await message.reply(f"⚠️ 系統異常，錯誤代碼：{e}")

    await bot.process_commands(message)

if __name__ == "__main__":
    keep_alive()
    bot.run(DISCORD_BOT_TOKEN)
