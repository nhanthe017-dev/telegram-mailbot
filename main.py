from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from flask import Flask, request
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from email.mime.image import MIMEImage
import re
import os

# =============== CẤU HÌNH ===============
BOT_TOKEN = "7965854829:AAGQ8Y3mTi_0719bbSrf-sAMV6H2sG5of7Q"
WEBHOOK_URL = "https://your-render-app-name.onrender.com/webhook"  # ⚠️ Sửa lại URL này
SENDER_EMAIL = "bankm7247@gmail.com"
SENDER_NAME = "MB eBanking"
PASSWORD = "jvsk apqd udzn unaf"
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

async def send_email(data):
    tenbank = data.get("tenbank", "")
    tienback = int(data.get("tienback", 0))
    mailsend = data.get("mailsend", "")
    timeGiaoDich = data.get("timeGiaoDich", "")
    ngayketthuc = data.get("ngayketthuc", "")
    tongkeo = format_vnd(int(data.get("tongkeo", 0)))

    msg = MIMEMultipart("related")
    msg["Subject"] = "THÔNG BÁO TREO GIAO DỊCH"
    msg["From"] = formataddr((SENDER_NAME, SENDER_EMAIL))
    msg["To"] = mailsend

    tienchuyen = format_vnd(tienback)

    html = f"""
    <html>
      <body style="font-family: Arial, Verdana, sans-serif; margin:0; padding:0;">
        <div style="max-width:600px; margin:auto; padding:0;">
          <p style="font-size:16px; font-weight:bold; margin:3px 0 3px 0;">
            Kính gửi Quý khách hàng <span style="text-transform:uppercase;">{tenbank}</span>
          </p>
          <div style="margin-bottom:18px;">
            <img src="cid:logo1" style="width:100%; max-width:600px; display:block; margin:0 auto;"/>
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
            <img src="cid:footer" style="width:100%; max-width:600px; display:block; margin:0 auto;"/>
          </div>
        </div>
      </body>
    </html>
    """

    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with open("image/logo1.png", "rb") as img:
            logo = MIMEImage(img.read())
            logo.add_header("Content-ID", "<logo1>")
            msg.attach(logo)
    except FileNotFoundError:
        pass

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, PASSWORD)
        server.sendmail(SENDER_EMAIL, mailsend, msg.as_string())

async def sendmail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = " ".join(context.args)
        if not text:
            await update.message.reply_text("⚠️ Thiếu tham số. Gõ /huongdan để xem hướng dẫn.")
            return

        parts = re.split(r" (?=\w+=)", text.strip())
        data = {k: v for k, v in (p.split("=", 1) for p in parts if "=" in p)}

        data["tienback"] = int(data["tienback"].replace(",", "").replace(".", ""))
        data["tongkeo"] = int(data["tongkeo"].replace(",", "").replace(".", ""))

        await update.message.reply_text("⏳ Đang gửi email...")
        await send_email(data)
        await update.message.reply_text("✅ Đã gửi email thành công!")

        if ADMIN_CHAT_ID:
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Người dùng vừa gửi email tới {data['mailsend']}")
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi: {e}")

# =============== CHẠY BOT (WEBHOOK MODE) ===============
flask_app = Flask(__name__)
application = Application.builder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("sendmail", sendmail))
application.add_handler(CommandHandler("huongdan", huongdan))

@flask_app.route("/webhook", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    await application.process_update(update)
    return "ok"

@flask_app.route("/")
def index():
    return "✅ Bot đang chạy với webhook."

async def main():
    await application.bot.set_webhook(WEBHOOK_URL)
    print("🚀 Webhook đã được thiết lập:", WEBHOOK_URL)

if __name__ == "__main__":
    asyncio.run(main())
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
