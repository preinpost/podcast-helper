from loguru import logger
import os
from io import BytesIO
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from pkg.openai import create_openai_client, analyze_text, analyze_image
# from pkg.xai import create_xai_client, analyze_text, analyze_image
MAX_MESSAGE_LENGTH = 4096  # Telegram 메시지 최대 길이


# 헬퍼 함수들
def _is_user_allowed(user_id: int, allowed_user_ids: set[int]) -> bool:
    """사용자가 봇 사용 권한이 있는지 확인"""
    if not allowed_user_ids:
        return True
    return user_id in allowed_user_ids


async def _send_long_message(update: Update, text: str):
    """긴 메시지를 여러 개로 나누어 전송"""
    if not update.message:
        return

    if len(text) <= MAX_MESSAGE_LENGTH:
        await update.message.reply_text(text)
        return

    parts = []
    current_part = ""

    lines = text.split("\n")
    for line in lines:
        if len(current_part) + len(line) + 1 <= MAX_MESSAGE_LENGTH:
            if current_part:
                current_part += "\n" + line
            else:
                current_part = line
        else:
            if current_part:
                parts.append(current_part)

            if len(line) > MAX_MESSAGE_LENGTH:
                for i in range(0, len(line), MAX_MESSAGE_LENGTH):
                    parts.append(line[i : i + MAX_MESSAGE_LENGTH])
                current_part = ""
            else:
                current_part = line

    if current_part:
        parts.append(current_part)

    for i, part in enumerate(parts, 1):
        if len(parts) > 1:
            header = f"[{i}/{len(parts)}]\n\n"
            await update.message.reply_text(header + part)
        else:
            await update.message.reply_text(part)


# 핸들러 함수들
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """봇 시작 명령어 처리"""
    if update.effective_user is None:
        raise ValueError("Effective user is None")

    if update.message is None:
        return

    allowed_user_ids = context.bot_data["allowed_user_ids"]
    user_id = update.effective_user.id
    logger.info(f"User {user_id} started the bot.")

    if not _is_user_allowed(user_id, allowed_user_ids):
        logger.warning(f"Unauthorized access attempt by user {user_id}")
        await update.message.reply_text(
            "죄송합니다. 이 봇은 인증된 사용자만 사용할 수 있습니다.\n"
            f"당신의 User ID: {user_id}"
        )
        return

    welcome_message = """안녕하세요! 팟캐스트 영어 학습 도우미입니다.

사용법:
1. 팟캐스트 전사문 텍스트를 보내주세요
2. 또는 전사문 캡처 이미지를 보내주세요

전사문을 분석해서 주요 어휘, 문법, 발음 팁을 제공해드립니다!"""
    await update.message.reply_text(welcome_message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """도움말 명령어 처리"""
    if update.effective_user is None:
        raise ValueError("Effective user is None")

    if update.message is None:
        return

    allowed_user_ids = context.bot_data["allowed_user_ids"]
    user_id = update.effective_user.id

    if not _is_user_allowed(user_id, allowed_user_ids):
        logger.warning(f"Unauthorized access attempt by user {user_id}")
        await update.message.reply_text(
            "죄송합니다. 이 봇은 인증된 사용자만 사용할 수 있습니다.\n"
            f"당신의 User ID: {user_id}"
        )
        return

    help_message = """사용 가능한 명령어:
/start - 봇 시작
/help - 도움말 보기

팟캐스트 전사문을 텍스트나 이미지로 보내면 분석해드립니다."""
    await update.message.reply_text(help_message)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """텍스트 메시지 처리"""
    ai_client = context.bot_data["ai_client"]
    allowed_user_ids = context.bot_data["allowed_user_ids"]

    if update.effective_user is None:
        raise ValueError("Effective user is None")

    if update.message is None:
        return

    user_id = update.effective_user.id
    user_text = update.message.text

    if user_text is None:
        return

    logger.info(f"Received text from user {user_id}")

    if not _is_user_allowed(user_id, allowed_user_ids):
        logger.warning(f"Unauthorized access attempt by user {user_id}")
        await update.message.reply_text(
            "죄송합니다. 이 봇은 인증된 사용자만 사용할 수 있습니다.\n"
            f"당신의 User ID: {user_id}"
        )
        return

    await update.message.reply_text("전사문을 분석하고 있습니다...")

    try:
        analysis = await analyze_text(user_text, ai_client)

        if analysis is None:
            raise ValueError("AI 분석 결과가 없습니다.")

        await _send_long_message(update, analysis)
    except Exception as e:
        logger.error(f"Error analyzing text: {e}")
        await update.message.reply_text("분석 중 오류가 발생했습니다. 다시 시도해주세요.")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """이미지 메시지 처리"""
    ai_client = context.bot_data["ai_client"]
    allowed_user_ids = context.bot_data["allowed_user_ids"]

    if update.effective_user is None:
        raise ValueError("Effective user is None")

    if update.message is None:
        return

    user_id = update.effective_user.id
    logger.info(f"Received photo from user {user_id}")

    if not _is_user_allowed(user_id, allowed_user_ids):
        logger.warning(f"Unauthorized access attempt by user {user_id}")
        await update.message.reply_text(
            "죄송합니다. 이 봇은 인증된 사용자만 사용할 수 있습니다.\n"
            f"당신의 User ID: {user_id}"
        )
        return

    await update.message.reply_text("이미지를 분석하고 있습니다...")

    try:
        photo = update.message.photo[-1]
        photo_file = await photo.get_file()

        image_bytes = BytesIO()
        await photo_file.download_to_memory(image_bytes)
        image_bytes.seek(0)

        analysis = await analyze_image(image_bytes.read(), ai_client)
        if analysis:
            await _send_long_message(update, analysis)
        else:
            raise ValueError("AI 분석 결과가 없습니다.")
    except Exception as e:
        logger.error(f"Error analyzing image: {e}")
        await update.message.reply_text(
            "이미지 분석 중 오류가 발생했습니다. 다시 시도해주세요."
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """전역 에러 핸들러"""
    logger.error(
        f"Exception while handling an update: {context.error}", exc_info=context.error
    )

    if isinstance(update, Update) and update.message:
        try:
            await update.message.reply_text(
                "예상치 못한 오류가 발생했습니다. 다시 시도해주세요."
            )
        except Exception as e:
            logger.error(f"Error sending error message: {e}")


async def post_init(application: Application):
    """
    봇이 시작되고 이벤트 루프가 돌아가기 시작한 직후에 실행됩니다.
    여기서 비동기 클라이언트(AI Client 등)를 생성해야
    올바른 이벤트 루프에 연결됩니다.
    """
    logger.info("Initializing AI Client inside the event loop...")
    # 여기서 client를 생성하여 bot_data에 넣습니다.
    application.bot_data["ai_client"] = create_openai_client()
    

def bot_init() -> Application:
    """봇 초기화 함수"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")

    allowed_ids = os.getenv("ALLOWED_USER_IDS", "")
    allowed_user_ids = set()
    if allowed_ids:
        allowed_user_ids = {
            int(uid.strip()) for uid in allowed_ids.split(",") if uid.strip()
        }

    logger.info(
        f"Allowed user IDs: {allowed_user_ids if allowed_user_ids else 'All users'}"
    )

    application = Application.builder().token(token).post_init(post_init).build()

    # bot_data에 저장 (global 대신)
    application.bot_data["allowed_user_ids"] = allowed_user_ids

    # 핸들러 등록
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_error_handler(error_handler)

    return application


def run_bot():
    """봇 실행"""
    logger.info("Starting bot...")
    app = bot_init()
    app.run_polling(allowed_updates=Update.ALL_TYPES)
