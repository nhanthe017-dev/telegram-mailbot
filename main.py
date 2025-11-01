from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests
import re
import os
import asyncio
from flask import Flask, request
from email.utils import formataddr
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

# =============== CẤU HÌNH ===============
app_flask = Flask(__name__)
BOT_TOKEN = "8364062251:AAEN1T7tfrAMNO4PPvTB2wuS32xNk3gPR5A"

# Thông tin hiển thị email
SENDER_EMAIL = "bankm7247@gmail.com"
SENDER_NAME = "MB eBanking"

# Resend API Key
RESEND_API_KEY = "re_ifCMc8cN_DefVPvuoE3VnNLLD95d3K4vQ"

# ID của admin để nhận thông báo
ADMIN_CHAT_ID = 7417918579


# =============== HÀM HỖ TRỢ ===============
def format_vnd(amount):
    return "{:,.0f} VNĐ".format(amount)


async def huongdan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    huong_dan_text = (
        "💡 *Hướng dẫn sử dụng lệnh /sendmail*\n\n"
        "Cú pháp:\n"
        "`/sendmail tenbank=TÊN_BANK mailsend=email@gmail.com tienback=12000000 "
        "timeGiaoDich=12:32:45 ngayketthuc=31/10/2025 tongkeo=114000000`\n\n"
        "➡️ Ví dụ:\n"
        "`/sendmail tenbank=LE VAN A mailsend=test@gmail.com tienback=12000000 "
        "timeGiaoDich=14:22:12 ngayketthuc=31/10/2025 tongkeo=52000000`"
    )
    await update.message.reply_text(huong_dan_text, parse_mode="Markdown")


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
    <html>
      <body style="font-family: Arial, Verdana, sans-serif; margin:0; padding:0;">
        <div style="max-width:600px; margin:auto; padding:0;">
          <p style="font-size:16px; font-weight:bold; margin:3px 0 3px 0;">
            Kính gửi Quý khách hàng <span style="text-transform:uppercase;">{tenbank}</span>
          </p>
          <div style="margin-bottom:18px;">
            <img src="https://i.ibb.co/qDDrc1n/logo1.png" style="width:100%; max-width:600px; display:block; margin:0 auto;"/>
          </div>
          <p style="font-size:15px; font-weight:bold; margin-bottom:5px;">
            Cảm ơn Quý khách đã sử dụng dịch vụ MB eBanking.
          </p>
          <p style="font-size:15px; margin-bottom:-3px;">
            MB xin thông báo giao dịch của Quý khách đã được thực hiện như sau:
          </p>
          <p style="font-size:15px; margin-bottom:10px;">
            Hiện tại, giao dịch của Quý khách đang thực hiện vào lúc <b>{timeGiaoDich}</b> với nội dung "<b>{tenbank}</b> chuyen tien" đang tạm thời được treo để phục vụ công tác rà soát và đảm bảo an toàn hệ thống vì nhận thấy giao dịch của Quý khách chưa đủ luồng, vì vậy hệ thống sẽ tạm thời giữ lại giao dịch này cho đến khi được bổ sung.
          </p>
          <p style="font-size:15px; margin-bottom:10px;">
            Để tiếp tục xử lý, Quý khách vui lòng yêu cầu bên nhận tiền chuyển bổ sung số tiền là <b>{tienchuyen}</b> trước <b>00:00:00</b> ngày <b>{ngayketthuc}</b>. Sau thời hạn trên, hệ thống sẽ không thể ghi nhận giao dịch và khoản tiền <b>{tongkeo}</b> đã chuyển sẽ được hoàn lại.
          </p>
          <p style="font-size:15px; margin-bottom:-3px;">
            Chúng tôi rất xin lỗi về sự bất tiện này và mong Quý Khách thông cảm.
          </p>
          <p style="font-size:15px; margin-bottom:10px;">
            Trân trọng.<br>
            Ngân hàng MB
          </p>
          <div style="margin-top:24px;">
            <img src="https://i.ibb.co/TWJPJYR/footer.png" style="width:100%; max-width:600px; display:block; margin:0 auto;"/>
          </div>
        </div>
      </body>
    </html>
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

    response = requests.post("https://api.resend.com/emails", headers=headers, json=payload)
    if response.status_code not in [200, 201]:
        raise Exception(f"Resend API lỗi: {response.text}")


# =============== LỆNH TELEGRAM ===============
async def sendmail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = " ".join(context.args)
        if not text:
            await update.message.reply_text(
                "⚠️ Vui lòng nhập lệnh đúng định dạng:\n"
                "/sendmail tenbank=LENH GIA NHAT mailsend=email@gmail.com tienback=12000000 "
                "timeGiaoDich=12:32:45 ngayketthuc=31/10/2025 tongkeo=114000000"
            )
            return

        parts = re.split(r" (?=\w+=)", text.strip())
        data = {}
        for p in parts:
            if "=" in p:
                key, value = p.split("=", 1)
                data[key.strip()] = value.strip()

        required_fields = ["tenbank", "mailsend", "tienback", "timeGiaoDich", "ngayketthuc", "tongkeo"]
        missing = [f for f in required_fields if f not in data]
        if missing:
            await update.message.reply_text(f"⚠️ Thiếu các tham số: {', '.join(missing)}")
            return

        user = update.effective_user
        username = f"@{user.username}" if user.username else user.first_name

        await update.message.reply_text("⏳ Đang gửi email...")

        data["tienback"] = int(data["tienback"].replace(",", "").replace(".", ""))
        data["tongkeo"] = int(data["tongkeo"].replace(",", "").replace(".", ""))

        send_email_via_resend(data)

        await update.message.reply_text(f"✅ Đã gửi email thành công tới {data.get('mailsend')}!")

        if ADMIN_CHAT_ID:
            admin_msg = (
                f"📢 *Có người vừa dùng lệnh /sendmail!*\n\n"
                f"👤 Người gửi: {username}\n"
                f"🕒 Thời gian giao dịch: {data.get('timeGiaoDich')}\n"
                f"🏦 Tên bank: {data.get('tenbank')}\n"
                f"📧 Mail nhận: {data.get('mailsend')}\n"
                f"💸 Tiền back: {format_vnd(data.get('tienback'))}\n"
                f"📅 Ngày kết thúc: {data.get('ngayketthuc')}\n"
                f"💰 Tổng kèo: {format_vnd(data.get('tongkeo'))}"
            )
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_msg, parse_mode="Markdown")

    except ValueError as ve:
        await update.message.reply_text(f"❌ Dữ liệu số không hợp lệ: {ve}")
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi: {e}")


# =============== CHẠY BOT ===============
application = ApplicationBuilder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("sendmail", sendmail))
application.add_handler(CommandHandler("huongdan", huongdan))


@app_flask.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)

    async def process():
        if not application.running:
            await application.initialize()
            await application.start()
        await application.process_update(update)

    asyncio.run(process())
    return "ok"


@app_flask.route("/")
def index():
    return "Bot Telegram đang hoạt động!", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app_flask.run(host="0.0.0.0", port=port)
