"""
Telegram Interface Module — FR-03, NFR-SEC-02, NFR-USA-01/02
- Sends generated drafts with Approve / Reject inline buttons
- Handles callback queries from owner
- Each owner instance is isolated by bot token + chat_id

KURULUM ADIMLARI:
1. Telegram'da @BotFather'a git
2. /newbot komutunu çalıştır, bot adı ver
3. Aldığın token'ı .env dosyasında TELEGRAM_BOT_TOKEN'a yaz
4. Telegram'da @userinfobot'a herhangi bir mesaj at
5. Sana dönen 'Id' değerini TELEGRAM_OWNER_CHAT_ID'ye yaz
"""
import json
import logging

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application, CallbackQueryHandler, CommandHandler,
    MessageHandler, filters, ContextTypes
)

from config import settings
from database import SessionLocal, Post

logger = logging.getLogger(__name__)


def _format_draft(post: Post) -> str:
    hashtags = " ".join(post.hashtags_list())
    post_time = post.post_time.strftime("%d %b %Y %H:%M") if post.post_time else "Belirlenmedi"
    return (
        f"📝 *Yeni İçerik Taslağı* (ID: {post.id})\n\n"
        f"📱 Platform: *{post.platform.upper()}*\n"
        f"🎭 Ton: _{post.tone}_\n\n"
        f"─────────────────────────\n"
        f"{post.caption}\n\n"
        f"{hashtags}\n"
        f"─────────────────────────\n"
        f"🖼 Görsel öneri: _{post.image_suggestion}_\n"
        f"🕐 Planlanan yayın: {post_time}"
    )


def _approval_keyboard(post_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Onayla", callback_data=f"approve:{post_id}"),
            InlineKeyboardButton("❌ Reddet", callback_data=f"reject:{post_id}"),
        ]
    ])


async def send_draft_to_owner(post: Post) -> None:
    """Send a generated draft to the owner for approval (NFR-USA-02)."""
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_OWNER_CHAT_ID:
        logger.warning("Telegram not configured — skipping draft delivery")
        return

    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    text = _format_draft(post)
    keyboard = _approval_keyboard(post.id)

    message = await bot.send_message(
        chat_id=settings.TELEGRAM_OWNER_CHAT_ID,
        text=text,
        parse_mode="Markdown",
        reply_markup=keyboard,
    )

    # Save message_id so we can update it later
    db = SessionLocal()
    try:
        db_post = db.query(Post).filter(Post.id == post.id).first()
        if db_post:
            db_post.telegram_message_id = message.message_id
            db.commit()
    finally:
        db.close()

    logger.info("Draft (post_id=%d) sent to Telegram chat %s", post.id, settings.TELEGRAM_OWNER_CHAT_ID)


async def notify_owner(message: str) -> None:
    """Send a plain-language notification to the owner (NFR-USA-03)."""
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_OWNER_CHAT_ID:
        return
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    await bot.send_message(
        chat_id=settings.TELEGRAM_OWNER_CHAT_ID,
        text=message,
        parse_mode="Markdown",
    )


# ── Bot Application (long-polling, run separately or in thread) ───────────────

async def _start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Merhaba! Ben AI Sosyal Medya Asistanınım.\n\n"
        "İçerik oluşturmak için doğrudan bir mesaj gönder.\n"
        "Örnek: _Yarın Latin gecemiz var._",
        parse_mode="Markdown",
    )


async def _handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner sends a prompt via Telegram → triggers the full pipeline."""
    # Validate that only the configured owner can trigger generation
    if str(update.effective_chat.id) != str(settings.TELEGRAM_OWNER_CHAT_ID):
        await update.message.reply_text("⛔ Yetkisiz erişim.")
        return

    prompt = update.message.text.strip()
    if not prompt:
        return

    await update.message.reply_text("⏳ İçerik oluşturuluyor, lütfen bekleyin...")

    try:
        from agents.orchestrator import orchestrator
        from database import SessionLocal
        db = SessionLocal()
        try:
            post = orchestrator.run(
                db=db,
                tenant_id=settings.DEFAULT_TENANT_ID,
                prompt=prompt,
                platform="instagram",
                send_telegram=True,
            )
        finally:
            db.close()
    except Exception as e:
        logger.error("Pipeline error from Telegram trigger: %s", e)
        await update.message.reply_text(
            f"⚠️ İçerik oluşturulurken bir hata oluştu.\n_{str(e)}_",
            parse_mode="Markdown",
        )


async def _handle_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Approve / Reject button presses."""
    query = update.callback_query
    await query.answer()

    # Security: only the configured owner chat can approve
    if str(query.message.chat.id) != str(settings.TELEGRAM_OWNER_CHAT_ID):
        await query.edit_message_text("⛔ Yetkisiz erişim.")
        return

    action, post_id_str = query.data.split(":", 1)
    post_id = int(post_id_str)

    db = SessionLocal()
    try:
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            await query.edit_message_text("❌ Gönderi bulunamadı.")
            return

        if action == "approve":
            post.status = "approved"
            db.commit()
            await query.edit_message_text(
                f"✅ *Onaylandı!* (ID: {post_id})\n\n"
                f"Gönderi yayın kuyruğuna alındı.\n"
                f"Planlanan: {post.post_time.strftime('%d %b %Y %H:%M') if post.post_time else 'Hemen'}",
                parse_mode="Markdown",
            )
            logger.info("Post %d approved by owner", post_id)

        elif action == "reject":
            post.status = "rejected"
            db.commit()
            await query.edit_message_text(
                f"❌ *Reddedildi* (ID: {post_id})\n\n"
                f"Taslak kaydedildi. Yeni içerik için yeni bir istek gönder.",
                parse_mode="Markdown",
            )
            logger.info("Post %d rejected by owner", post_id)
    finally:
        db.close()


def build_application() -> Application:
    """Build and return the Telegram bot Application."""
    app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", _start))
    app.add_handler(CallbackQueryHandler(_handle_approval))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _handle_text))
    return app


def run_bot():
    """Start the Telegram bot in long-polling mode. Run in a separate thread."""
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not set — bot will not start")
        return
    app = build_application()
    logger.info("Telegram bot starting...")
    app.run_polling(drop_pending_updates=True)
