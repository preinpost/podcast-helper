# -*- coding: utf-8 -*-
import logging
import os
from io import BytesIO
from functools import wraps
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from pkg.ai import AIClient

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class PodcastHelperBot:
    MAX_MESSAGE_LENGTH = 4096  # Telegram 메시지 최대 길이

    def __init__(self):
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")

        # 허용된 사용자 ID 로드
        allowed_ids = os.getenv("ALLOWED_USER_IDS", "")
        self.allowed_user_ids = set()
        if allowed_ids:
            self.allowed_user_ids = {int(uid.strip()) for uid in allowed_ids.split(",") if uid.strip()}

        logger.info(f"Allowed user IDs: {self.allowed_user_ids if self.allowed_user_ids else 'All users'}")

        self.ai_client = AIClient()
        self.application = Application.builder().token(token).build()

        # 핸들러 등록
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        self.application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))

    def is_user_allowed(self, user_id: int) -> bool:
        """사용자가 봇 사용 권한이 있는지 확인"""
        # 허용된 사용자 ID가 설정되지 않았으면 모든 사용자 허용
        if not self.allowed_user_ids:
            return True
        return user_id in self.allowed_user_ids

    async def send_long_message(self, update: Update, text: str):
        """긴 메시지를 여러 개로 나누어 전송"""
        if len(text) <= self.MAX_MESSAGE_LENGTH:
            await update.message.reply_text(text)
            return

        # 메시지를 최대 길이로 나누기
        parts = []
        current_part = ""

        # 줄 단위로 나누어서 최대한 자연스럽게 분할
        lines = text.split('\n')
        for line in lines:
            # 현재 파트에 이 줄을 추가해도 최대 길이를 넘지 않는 경우
            if len(current_part) + len(line) + 1 <= self.MAX_MESSAGE_LENGTH:
                if current_part:
                    current_part += '\n' + line
                else:
                    current_part = line
            else:
                # 현재 파트를 저장하고 새 파트 시작
                if current_part:
                    parts.append(current_part)

                # 한 줄 자체가 최대 길이를 넘는 경우 강제로 자르기
                if len(line) > self.MAX_MESSAGE_LENGTH:
                    for i in range(0, len(line), self.MAX_MESSAGE_LENGTH):
                        parts.append(line[i:i + self.MAX_MESSAGE_LENGTH])
                    current_part = ""
                else:
                    current_part = line

        # 마지막 파트 추가
        if current_part:
            parts.append(current_part)

        # 모든 파트 전송
        for i, part in enumerate(parts, 1):
            if len(parts) > 1:
                # 여러 파트로 나뉜 경우 파트 번호 표시
                header = f"[{i}/{len(parts)}]\n\n"
                await update.message.reply_text(header + part)
            else:
                await update.message.reply_text(part)

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """봇 시작 명령어 처리"""
        user_id = update.effective_user.id
        logger.info(f"User {user_id} started the bot.")

        if not self.is_user_allowed(user_id):
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

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """도움말 명령어 처리"""
        user_id = update.effective_user.id

        if not self.is_user_allowed(user_id):
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

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """텍스트 메시지 처리"""
        user_id = update.effective_user.id
        user_text = update.message.text
        logger.info(f"Received text from user {user_id}")

        if not self.is_user_allowed(user_id):
            logger.warning(f"Unauthorized access attempt by user {user_id}")
            await update.message.reply_text(
                "죄송합니다. 이 봇은 인증된 사용자만 사용할 수 있습니다.\n"
                f"당신의 User ID: {user_id}"
            )
            return

        await update.message.reply_text("전사문을 분석하고 있습니다...")

        try:
            analysis = self.ai_client.analyze_text(user_text)
            await self.send_long_message(update, analysis)
        except Exception as e:
            logger.error(f"Error analyzing text: {e}")
            await update.message.reply_text(
                "분석 중 오류가 발생했습니다. 다시 시도해주세요."
            )

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """이미지 메시지 처리"""
        user_id = update.effective_user.id
        logger.info(f"Received photo from user {user_id}")

        if not self.is_user_allowed(user_id):
            logger.warning(f"Unauthorized access attempt by user {user_id}")
            await update.message.reply_text(
                "죄송합니다. 이 봇은 인증된 사용자만 사용할 수 있습니다.\n"
                f"당신의 User ID: {user_id}"
            )
            return

        await update.message.reply_text("이미지를 분석하고 있습니다...")

        try:
            # 가장 큰 크기의 이미지 가져오기
            photo = update.message.photo[-1]
            photo_file = await photo.get_file()

            # 이미지 다운로드
            image_bytes = BytesIO()
            await photo_file.download_to_memory(image_bytes)
            image_bytes.seek(0)

            # AI 분석
            analysis = self.ai_client.analyze_image(image_bytes.read())
            await self.send_long_message(update, analysis)
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            await update.message.reply_text(
                "이미지 분석 중 오류가 발생했습니다. 다시 시도해주세요."
            )

    def run(self):
        """봇 실행"""
        logger.info("Starting bot...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
