import os
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread
import google.generativeai as genai

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

# 🌟 用來存放每個人「專屬記憶」的字典
user_chats = {}

@bot.event
async def on_ready():
    print(f"✅ 機器人已成功啟動並登入為 {bot.user}")

# ==========================================
# 3. 具備記憶力、極致穩定的 AI 大腦
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
            async with message.channel.typing():
                user_id = message.author.id

                # 如果是新對話，開啟專屬記憶聊天室
                if user_id not in user_chats:
                    system_prompt = (
                        "你現在是一個精通世界盃足球賽與台灣運彩盤口的超強分析師。"
                        "請根據你龐大的內建體育資料庫，用專業、精準但帶點幽默的語氣回答用戶。"
                        "請分析近期戰力，並給出具體的下注建議，告訴用戶下哪個期望值最高。"
                        "結尾請加一句幽默的警語，例如：『球是圓的，運彩有賺有賠，請量力而為啊！』"
                    )
                    
                    # 使用穩定的舊版呼叫法與最新 2.5 模型，捨棄衝突的外掛
                    model = genai.GenerativeModel(
                        model_name='gemini-2.5-flash',
                        system_instruction=system_prompt
                    )
                    user_chats[user_id] = model.start_chat(history=[])

                # 💡 關鍵修復：這裡改用「同步」發送訊息，徹底避開 aiohttp 的異步報錯地雷
                response = user_chats[user_id].send_message(user_input)
                
                await message.reply(response.text)
                
        except Exception as e:
            await message.reply(f"⚠️ 系統異常，錯誤代碼：{e}")

    await bot.process_commands(message)

# ==========================================
# 4. 啟動區塊
# ==========================================
if __name__ == "__main__":
    keep_alive()
    bot.run(DISCORD_BOT_TOKEN)
