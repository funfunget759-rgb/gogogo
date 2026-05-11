import os
import asyncio
import logging
from flask import Flask
from threading import Thread
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# 1. 建立一個簡單的 Web 伺服器防止 Render 休眠
app = Flask('')
@app.route('/')
def home():
    return "Bot is alive!"

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# 2. 機器人核心邏輯
logging.basicConfig(level=logging.INFO)

async def download_and_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "instagram.com" not in url and "threads.net" not in url:
        return

    wait_msg = await update.message.reply_text("⏳ 正在讀取內容，請稍候...")
    
    # yt-dlp 設定
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloaded_media.%(ext)s',
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        if filename.endswith(('.mp4', '.mov')):
            await update.message.reply_video(video=open(filename, 'rb'))
        else:
            await update.message.reply_photo(photo=open(filename, 'rb'))
        
        if os.path.exists(filename):
            os.remove(filename)
        await wait_msg.delete()

    except Exception as e:
        await wait_msg.edit_text(f"❌ 解析失敗。原因：{str(e)}")

if __name__ == '__main__':
    # 啟動 Web 伺服器
    Thread(target=run_web).start()
    
    # 啟動 Bot
    token = os.environ.get("BOT_TOKEN")
    app_bot = ApplicationBuilder().token(token).build()
    app_bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), download_and_send))
    
    print("Bot is running...")
    app_bot.run_polling()
