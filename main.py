import os
import asyncio
import logging
from flask import Flask
from threading import Thread
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# 1. 建立 Web 伺服器 (供 Render 存活監測及 UptimeRobot 使用)
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run_web():
    # Render 會自動分配 PORT，若無則預設 8080
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# 2. 機器人核心邏輯設定
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def download_and_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    
    # 只處理 IG 和 Threads 連結
    if "instagram.com" not in url and "threads.net" not in url:
        return

    # 發送讀取中狀態
    wait_msg = await update.message.reply_text("⏳ 幫緊你呀,柒頭...")
    
    # yt-dlp 下載設定
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloaded_media.%(ext)s', # 檔案暫存名稱
        'quiet': True,
        'no_warnings': True,
    }

    try:
        # 開始下載
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        # 根據檔案格式發送 (加上你要求的 Caption)
        if filename.endswith(('.mp4', '.mov', '.m4v')):
            await update.message.reply_video(
                video=open(filename, 'rb'), 
                caption="柒頭睇野啦!"
            )
        else:
            await update.message.reply_photo(
                photo=open(filename, 'rb'), 
                caption="柒頭睇野啦!"
            )
        
        # 發送成功後刪除伺服器上的暫存檔
        if os.path.exists(filename):
            os.remove(filename)
            
        # 刪除「幫緊你呀」的提示訊息
        await wait_msg.delete()

    except Exception as e:
        logging.error(f"Error: {e}")
        await wait_msg.edit_text(f"❌ 頂，解析唔到。原因：{str(e)}")

if __name__ == '__main__':
    # A. 先在後台啟動 Flask 網頁伺服器
    Thread(target=run_web).start()
    
    # B. 啟動 Telegram Bot
    token = os.environ.get("BOT_TOKEN")
    if not token:
        print("錯誤：找不到 BOT_TOKEN 環境變數！")
    else:
        app_bot = ApplicationBuilder().token(token).build()
        
        # 處理所有文字訊息（過濾掉指令）
        app_bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), download_and_send))
        
        print("Bot is running...")
        app_bot.run_polling()
