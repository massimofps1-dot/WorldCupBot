import os
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread

# 導入全新的 Google GenAI SDK
from google import genai
from google.genai import types

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
# 2. 機器人與全新 AI 核心設定
# ==========================================
DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 初始化全新的用戶端
ai_client = genai.Client(api_key=GEMINI_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 🌟 用來存放每個人「專屬記憶」的字典
user_chats = {}

@bot.event
async def on_ready():
    print(f"✅ 機器人已成功啟動並登入為 {bot.user}")

# ==========================================
# 3. 具備「聯網」與「記憶」的 AI 大腦
# ==========================================
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if bot.user.mentioned_in(message):
        user_input = message.content.replace(f'<@{bot.user.id}>', '').strip()

        if not user_input:
            await message.reply("你要問我什麼比賽的預測？直接說！")
            return

        try:
            # 讓 Discord 顯示「機器人正在輸入中...」
            async with message.channel.typing():
                user_id = message.author.id

                # 如果是新對話，使用新版 aio (非同步) 與 types.Tool 語法啟動聊天室
                if user_id not in user_chats:
                    system_prompt = (
                        "你現在是一個精通世界盃足球賽與台灣運彩盤口的超強分析師。"
                        "你具備上網查詢最新資訊的能力。請根據你查到的最新賽程、戰績或新聞，"
                        "用專業、精準但帶點幽默的語氣回答用戶。"
                        "請分析近期戰力，並給出具體的下注建議，告訴用戶下哪個期望值最高。"
                        "結尾請加一句幽默的警語，例如：『球是圓的，運彩有賺有賠，請量力而為啊！』"
                    )
                    
                    user_chats[user_id] = ai_client.aio.chats.create(
                        model='gemini-2.5-flash',
                        config=types.GenerateContentConfig(
                            system_instruction=system_prompt,
                            # 🌐 這裡就是官方最新且唯一支援的 Google 搜尋呼叫法
                            tools=[types.Tool(google_search=types.GoogleSearch())],
                            temperature=0.7
                        )
                    )

                # 傳送對話並取得回應
                response = await user_chats[user_id].send_message(user_input)
                
                # 回傳結果
                await message.reply(response.text)
                
        except Exception as e:
            await message.reply(f"⚠️ AI 腦袋暫時卡住了，錯誤代碼：{e}")

    await bot.process_commands(message)

# ==========================================
# 4. 啟動區塊
# ==========================================
if __name__ == "__main__":
    keep_alive()
    bot.run(DISCORD_BOT_TOKEN)
