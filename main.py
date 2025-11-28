# -*- coding: utf-8 -*-
import os
from dotenv import load_dotenv
from pkg.bot_v2 import run_bot


def main():
    # 환경 변수 로드
    load_dotenv()

    # 필수 환경 변수 확인
    required_vars = ["TELEGRAM_BOT_TOKEN", "OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        print("Please create a .env file based on .env.example")
        return

    # 봇 시작
    try:
        run_bot()
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
