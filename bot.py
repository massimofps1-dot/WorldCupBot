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

# 設定 Gemini AI 金鑰
genai.configure(api_key=GEMINI_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ 機器人已成功啟動並登入為 {bot.user}")

# ==========================================
# 3. 真正的 AI 對話大腦 (監聽 @標註)
# ==========================================
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # 只要有人 @標註 機器人，就會觸發真正的 AI 生成
    if bot.user.mentioned_in(message):
        # 過濾掉 @標記的文字，留下用戶真正說的話
        user_input = message.content.replace(f'<@{bot.user.id}>', '').strip()

        if not user_input:
            await message.reply("你要問我什麼比賽的預測？直接說！")
            return

        try:
            # 讓 Discord 顯示「機器人正在輸入中...」
            async with message.channel.typing():
                
                # 賦予 AI 「台灣運彩分析師」的人設與背景知識
                system_prompt = (
                    "你現在是一個精通 2026 世界盃足球賽與台灣運彩盤口的超強分析師。"
                    "請用專業、精準但帶點幽默的語氣回答用戶的預測問題。"
                    "你會分析兩隊近期戰力（如控球率、得失球），並給出『不讓分』、『讓分』或『大小分』的具體下注建議，告訴用戶下哪個期望值最高、比較賺。"
                    "結尾請務必加上一句幽默的警語，例如：『球是圓的，運彩有賺有賠，請量力而為啊！』"
                )
                
                # 呼叫 Gemini 1.5 Flash 模型
                model = genai.GenerativeModel(
                    model_name='gemini-1.5-flash',
                    system_instruction=system_prompt
                )
                
                # 異步請求 AI 生成回覆 (不卡死機器人)
                response = await model.generate_content_async(user_input)
                
                # 將 AI 的回答傳送回 Discord
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
