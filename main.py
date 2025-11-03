from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests
import re
import os
import asyncio
from flask import Flask, request
import nest_asyncio

nest_asyncio.apply()

# =============== CẤU HÌNH ===============
app_flask = Flask(__name__)
BOT_TOKEN = "8364062251:AAEN1T7tfrAMNO4PPvTB2wuS32xNk3gPR5A"

SENDER_EMAIL = "bankm7247@gmail.com"
SENDER_NAME = "MB eBanking"
RESEND_API_KEY = "re_ifCMc8cN_DefVPvuoE3VnNLLD95d3K4vQ"
ADMIN_CHAT_ID = 7417918579


# =============== HÀM HỖ TRỢ ===============
def format_vnd(amount):
    return "{:,.0f} VNĐ".format(amount)


async def huongdan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "💡 *Hướng dẫn sử dụng lệnh /sendmail*\n\n"
        "Cú pháp:\n"
        "`/sendmail tenbank=TÊN_BANK mailsend=email@gmail.com tienback=12000000 "
        "timeGiaoDich=12:32:45 ngayketthuc=31/10/2025 tongkeo=114000000`\n\n"
        "➡️ Ví dụ:\n"
        "`/sendmail tenbank=LE VAN A mailsend=test@gmail.com tienback=12000000 "
        "timeGiaoDich=14:22:12 ngayketthuc=31/10/2025 tongkeo=52000000`"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# =============== GỬI EMAIL QUA RESEND API ===============
def send_email_via_resend(data):
    tenbank = data.get("tenbank", "")
    tienback = int(data.get("tienback", 0))
    mailsend = data.get("mailsend", "")
    timeGiaoDich = data.get("timeGiaoDich", "")
    ngayketthuc = data.get("ngayketthuc", "")
    tongkeo = format_vnd(int(data.get("tongkeo", 0)))
    tienchuyen = format_vnd(tienback)

    html = f"""
    <html><body style="font-family: Arial;">
    <p>Kính gửi Quý khách hàng <b>{tenbank}</b></p>
    <p>Giao dịch của Quý khách đang tạm giữ tại {timeGiaoDich}, cần bổ sung {tienchuyen} trước {ngayketthuc}.</p>
    <p>Tổng giao dịch: {tongkeo}</p>
    <p>Trân trọng,<br>Ngân hàng MB</p>
    </body></html>
    """

    payload = {
        "from": f"{SENDER_NAME} <{SENDER_EMAIL}>",
        "to": [mailsend],
        "subject": "THÔNG BÁO TREO GIAO DỊCH",
        "html": html,
    }

    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json",
    }

    r = requests.post("https://api.resend.com/emails", headers=headers, json=payload)
    if r.status_code not in [200, 201]:
        raise Exception(f"Resend API lỗi: {r.text}")


# =============== LỆNH TELEGRAM ===============
async def sendmail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args_text = " ".join(context.args)
        if not args_text:
            await update.message.reply_text(
                "⚠️ Vui lòng nhập đúng cú pháp. Dùng /huongdan để xem ví dụ."
            )
            return

        parts = re.split(r" (?=\w+=)", args_text.strip())
        data = {k: v for k, v in (p.split("=", 1) for p in parts if "=" in p)}

        required = ["tenbank", "mailsend", "tienback", "timeGiaoDich", "ngayketthuc", "tongkeo"]
        missing = [f for f in required if f not in data]
        if missing:
            await update.message.reply_text(f"⚠️ Thiếu tham số: {', '.join(missing)}")
            return

        await update.message.reply_text("⏳ Đang gửi email...")

        data["tienback"] = int(data["tienback"].replace(",", "").replace(".", ""))
        data["tongkeo"] = int(data["tongkeo"].replace(",", "").replace(".", ""))

        send_email_via_resend(data)
        await update.message.reply_text(f"✅ Đã gửi email tới {data['mailsend']}!")

        # Gửi thông báo cho admin
        if ADMIN_CHAT_ID:
            msg = (
                f"📢 *Có người dùng /sendmail*\n\n"
                f"🏦 Tên bank: {data['tenbank']}\n"
                f"📧 Mail nhận: {data['mailsend']}\n"
                f"💸 Tiền back: {format_vnd(data['tienback'])}\n"
                f"📅 Ngày kết thúc: {data['ngayketthuc']}\n"
                f"💰 Tổng kèo: {format_vnd(data['tongkeo'])}"
            )
            await context.bot.send_message(ADMIN_CHAT_ID, msg, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi: {e}")


# =============== CHẠY BOT ===============
application = ApplicationBuilder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("sendmail", sendmail))
application.add_handler(CommandHandler("huongdan", huongdan))

# ✅ Tạo event loop riêng biệt cho Flask
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

@app_flask.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), application.bot)

        async def process():
            if not application.running:
                await application.initialize()
                await application.start()
            await application.process_update(update)

        asyncio.run_coroutine_threadsafe(process(), loop)
    except Exception as e:
        print("❌ Webhook error:", e)
    return "ok", 200


@app_flask.route("/")
def index():
    return "✅ Bot Telegram đang hoạt động!", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Bot đang chạy trên cổng {port}")
    app_flask.run(host="0.0.0.0", port=port, debug=False)
