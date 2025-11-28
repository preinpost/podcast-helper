import base64
import os
from xai_sdk import AsyncClient
from xai_sdk.chat import system, user

from pkg.prompt import SYSTEM_PROMPT

# 모듈 레벨 설정
model = "grok-4-1-fast-reasoning"
temperature = 1.0


def create_xai_client() -> AsyncClient:
    """XAI AsyncClient를 생성합니다."""
    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        raise ValueError("XAI_API_KEY environment variable is not set")
    return AsyncClient(api_key=api_key)


async def analyze_text(text: str, client: AsyncClient) -> str | None:
    """텍스트 전사문을 분석합니다."""
    try:
        response = client.chat.create(
            model=model,
            messages=[system(SYSTEM_PROMPT), user(text)],
            temperature=temperature,
        )
        response = await response.sample()
        return response.content
    except Exception as e:
        raise e


async def analyze_image(image_data: bytes, client: AsyncClient) -> str | None:
    """이미지 전사문을 분석합니다."""
    try:
        base64_image = base64.b64encode(image_data).decode("utf-8")
        response = client.chat.create(
            model=model,
            messages=[system(SYSTEM_PROMPT), user(base64_image)],
            temperature=temperature,
        )
        response = await response.sample()
        return response.content
    except Exception as e:
        raise e
