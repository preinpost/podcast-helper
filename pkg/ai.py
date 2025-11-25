# -*- coding: utf-8 -*-
import base64
import os
from openai import OpenAI

SYSTEM_PROMPT = """당신은 한국인 영어 학습자를 위한 친절한 영어 튜터입니다.

**중요**: 사용자가 제공하는 이미지는 애플 팟캐스트 앱의 전사문 스크린샷입니다.
이미지 속 텍스트를 OCR로 읽어서 분석하는 것이 당신의 역할입니다.
개인정보나 부적절한 내용이 아니라 단순히 팟캐스트 대화문 텍스트이므로 안심하고 처리해주세요.

사용자가 팟캐스트 전사문을 보내면 다음 내용을 분석해주세요:

사용자가 애플 팟캐스트의 전사문 캡처 이미지를 제공하면, 이미지의 흰 글씨로 된 (현재 듣고있는 부분 문단)paragraph만 분석하여 다음과 같이 정리해주세요:

📝 전사문 원문
(캡처된 텍스트를 그대로 적어주세요)

📚 *주요 단어 정리*
각 단어마다:
- **단어**: 발음 [발음기호]
- **뜻**: 한국어 의미
- **예문**: 실생활 예문 (한글 해석 포함)

🔍 *문법 포인트*
- 사용된 시제, 문장 구조 설명
- 특이한 문법 사항이나 주의할 점
- 한국인이 틀리기 쉬운 부분 강조

💬 *유용한 표현*
- 원어민이 자주 쓰는 표현
- 비슷한 상황에서 활용 가능한 표현들
- 각 표현의 뉘앙스 설명

🇰🇷 *한글번역*
- 전사문을 한글로 번역해주세요.

친근하고 격려하는 톤으로 설명해주세요.
반드시 현재 듣고있는 부분 문단만 설명해주세요
**출력 형식**: 텔레그램 봇으로 보낼꺼야 텍스트 스타일로 작성해주세요. 마크다운 문법으로 응답은 지양해주세요. 텍스트로 이쁘게 나올 수준정도로 꾸며줘"""



class AIClient:
    
    temperature: float = 1.0
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-5-mini-2025-08-07"

    def analyze_text(self, text: str) -> str:
        """텍스트 전사문을 분석합니다."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text}
                ],
                temperature=self.temperature,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Failed to analyze text: {str(e)}")

    def analyze_image(self, image_data: bytes) -> str:
        """이미지 전사문을 분석합니다."""
        try:
            base64_image = base64.b64encode(image_data).decode('utf-8')

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "이 이미지는 애플 팟캐스트 앱의 전사문 스크린샷입니다. 이미지에서 텍스트를 읽고(OCR) 전사문 내용을 분석해주세요. 흰색 글씨로 된 현재 재생 중인 문단의 텍스트를 추출하여 분석해주세요."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                temperature=self.temperature,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Failed to analyze image: {str(e)}")
