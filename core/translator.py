import re
import os
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
DTYPE = torch.float16 if torch.cuda.is_available() else torch.float32

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EN_RU_NAME = os.path.join(BASE_DIR, "models", "marian_en_ru")
RU_EN_NAME = "Helsinki-NLP/opus-mt-ru-en"


class LocalTranslator:
    def __init__(self):
        self.en_ru_model = None
        self.en_ru_tok = None
        self.ru_en_model = None
        self.ru_en_tok = None

    def _load_en_ru(self):
        if self.en_ru_model is None:
            self.en_ru_tok = AutoTokenizer.from_pretrained(EN_RU_NAME)
            self.en_ru_model = AutoModelForSeq2SeqLM.from_pretrained(
                EN_RU_NAME,
                torch_dtype=DTYPE
            ).to(DEVICE)

    def _load_ru_en(self):
        if self.ru_en_model is None:
            self.ru_en_tok = AutoTokenizer.from_pretrained(RU_EN_NAME)
            self.ru_en_model = AutoModelForSeq2SeqLM.from_pretrained(
                RU_EN_NAME,
                torch_dtype=DTYPE
            ).to(DEVICE)

    @staticmethod
    def is_cyrillic(text: str) -> bool:
        return bool(re.search(r"[\u0400-\u04FF]", text))

    def translate_ru_to_en(self, text: str) -> str:
        if not text.strip() or not self.is_cyrillic(text):
            return text

        self._load_ru_en()
        inputs = self.ru_en_tok(text, return_tensors="pt", padding=True, truncation=True, max_length=512).to(DEVICE)
        with torch.no_grad():
            outputs = self.ru_en_model.generate(**inputs, max_new_tokens=512)
        return self.ru_en_tok.decode(outputs[0], skip_special_tokens=True)

    def translate_en_to_ru(self, text: str) -> str:
        if not text.strip():
            return text

        self._load_en_ru()
        parts = re.split(r"(```[\s\S]*?```|`[^`\n]+`)", text)
        translated_parts = []

        for part in parts:
            if not part:
                continue
            if part.startswith("```") or part.startswith("`"):
                translated_parts.append(part)
                continue

            lines = part.split("\n")
            translated_lines = []
            for line in lines:
                if not line.strip():
                    translated_lines.append(line)
                    continue

                sentences = re.split(r"(?<=[.!?])\s+", line.strip())
                translated_sentences = []

                for sent in sentences:
                    if not sent.strip():
                        continue

                    inputs = self.en_ru_tok(
                        sent,
                        return_tensors="pt",
                        padding=True,
                        truncation=True,
                        max_length=512,
                    ).to(DEVICE)
                    with torch.no_grad():
                        outputs = self.en_ru_model.generate(
                            **inputs, max_new_tokens=512
                        )
                    res = self.en_ru_tok.decode(
                        outputs[0], skip_special_tokens=True
                    )
                    translated_sentences.append(res)

                translated_lines.append(" ".join(translated_sentences))

            translated_parts.append("\n".join(translated_lines))

        result = "".join(translated_parts)

        fixes = {
            "полуколонна": "точка с запятой",
            "полуколонны": "точки с запятой",
            "полуколонну": "точку с запятой",
            "бассейн нитей": "пул потоков",
            "нитка": "поток"
        }
        for wrong, right in fixes.items():
            result = re.sub(rf"\b{wrong}\b", right, result, flags=re.IGNORECASE)

        return result


translator = LocalTranslator()