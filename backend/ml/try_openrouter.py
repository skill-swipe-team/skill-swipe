"""Send a sample vacancy to OpenRouter and print extracted skills as JSON."""

import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROMPT_FILE = PROJECT_ROOT / "backend" / "ml" / "prompts" / "skill_extraction.md"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

VACANCY = """Ищем backend-разработчика для раннего стартапа в сфере онлайн-образования.
Нужно разработать REST API на Python и FastAPI, хранить данные в PostgreSQL,
упаковать сервис в Docker. Будет плюсом опыт с Redis и проектирование
асинхронных сервисов. Команда работает по Scrum.
"""


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    model = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat-v3.1")
    token = os.getenv("OPENROUTER_TOKEN")
    if not token:
        raise SystemExit(
            "Не задан OPENROUTER_TOKEN. Добавьте его в локальный .env "
            "или переменные окружения."
        )

    system_prompt = PROMPT_FILE.read_text(encoding="utf-8")
    payload = {
        "model": model,
        "temperature": 0,
        "max_tokens": 512,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Извлеки навыки из текста ниже.\n\n<text>\n{VACANCY}\n</text>",
            },
        ],
    }
    request = Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "Skill Swipe ML prompt test",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=60) as response:
            api_response = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise SystemExit(f"OpenRouter вернул HTTP {error.code}: {details}") from error
    except URLError as error:
        raise SystemExit(f"Не удалось подключиться к OpenRouter: {error.reason}") from error

    try:
        content = api_response["choices"][0]["message"]["content"]
        result = json.loads(content)
        if not isinstance(result, dict) or not isinstance(result.get("skills"), list):
            raise ValueError('Ожидался JSON-объект с массивом "skills".')
        if not all(isinstance(skill, str) for skill in result["skills"]):
            raise ValueError('Все элементы массива "skills" должны быть строками.')
    except (KeyError, IndexError, TypeError, json.JSONDecodeError, ValueError) as error:
        raise SystemExit(f"Не удалось разобрать ответ модели: {error}\nОтвет: {api_response}") from error

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
