# -*- coding: utf-8 -*-
import base64
import os
from openai import AsyncOpenAI

from pkg.prompt import SYSTEM_PROMPT

# 모듈 레벨 설정
model = "gpt-5-mini-2025-08-07"
temperature = 1.0


def create_openai_client() -> AsyncOpenAI:
    """OpenAI 클라이언트를 생성합니다."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    return AsyncOpenAI(api_key=api_key)


async def analyze_text(text: str, client: AsyncOpenAI) -> str | None:
    """텍스트 전사문을 분석합니다."""
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            temperature=temperature,
        )

        return response.choices[0].message.content

    except Exception as e:
        raise e


async def analyze_image(image_data: bytes, client: AsyncOpenAI) -> str | None:
    """이미지 전사문을 분석합니다."""
    try:
        base64_image = base64.b64encode(image_data).decode("utf-8")

        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "이 이미지는 애플 팟캐스트 앱의 전사문 스크린샷입니다. 이미지에서 텍스트를 읽고(OCR) 전사문 내용을 분석해주세요. 흰색 글씨로 된 현재 재생 중인 문단의 텍스트를 추출하여 분석해주세요.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                    ],
                },
            ],
            temperature=temperature,
        )
        return response.choices[0].message.content
    except Exception as e:
        raise e
