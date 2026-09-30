# 🧪 Screen Copilot — Model Fine-Tuning & Adaptation Pipeline

## EN version:

This branch focuses on the research side of the project: synthetic data preparation pipelines, token embedding calibration for the **Moondream2** multimodal model, and domain adaptation of the lightweight **MarianMT** translator for technical code.

---

## 🎯 Training Tasks

1. **Moondream2 (VLM) Special Token Calibration:**
   * Custom markup tokens (`<bbox>`, `</bbox>`, `<code_start>`, `<code_end>`, `<error_start>`, `<error_end>`, `<fix_start>`, `<fix_end>`) were injected into the tokenizer's vocabulary.
   * Training only affected the input embedding matrix in `bfloat16` mode, in order to link the text core with the visual encoder's coordinates without destabilizing the model's main weights.

2. **MarianMT (EN → RU) Domain Adaptation:**
   * The base `Helsinki-NLP/opus-mt-en-ru` model distorts technical terms and translates identifier names.
   * The Seq2Seq architecture was fine-tuned on a specialized corpus of pairs in order to enforce the invariance of syntactic constructs, data types, `snake_case`/`camelCase` variables, and code blocks.

---

## 📁 Branch Structure

```text
├── configs/
│   ├── embeddings.yaml       # Hyperparameters for the embedding matrix
│   └── marian.yaml           # Seq2Seq training parameters for the translator
├── data/
│   └── processed/            # Generated datasets (in .gitignore)
├── src/
│   ├── generate_marian_data.py # Synthetic EN-RU corpus generator
│   ├── train_embeddings.py     # Moondream2 embedding training pipeline
│   └── train_marian.py         # MarianMT fine-tuning script
├── outputs/                  # Saved checkpoints (in .gitignore)
└── run.py                    # Unified CLI dispatcher for launching training
```

---

## RU версия:

В этой ветке сосредоточена исследовательская часть проекта: пайплайны подготовки синтетических данных, калибровка токен-эмбеддингов для мультимодальной модели **Moondream2** и доменная адаптация легковесного переводчика **MarianMT** под технический код.

---

## 🎯 Задачи обучения

1. **Калибровка спецтокенов Moondream2 (VLM):**
   * В словарь токенизатора внедрены кастомные токены разметки (`<bbox>`, `</bbox>`, `<code_start>`, `<code_end>`, `<error_start>`, `<error_end>`, `<fix_start>`, `<fix_end>`).
   * Обучение затронуло только входную матрицу эмбеддингов в режиме `bfloat16`, чтобы связать текстовое ядро с координатами зрительного энкодера без расшатывания основных весов модели.

2. **Доменная адаптация MarianMT (EN → RU):**
   * Базовая модель `Helsinki-NLP/opus-mt-en-ru` искажает технические термины и переводит названия идентификаторов.
   * Выполнено дообучение Seq2Seq-архитектуры на специализированном корпусе пар, чтобы закрепить неизменность синтаксических конструкций, типов данных, `snake_case`/`camelCase` переменных и блоков кода.

---

## 📁 Структура ветки

```text
├── configs/
│   ├── embeddings.yaml       # Гиперпараметры для матрицы эмбеддингов
│   └── marian.yaml           # Параметры Seq2Seq обучения переводчика
├── data/
│   └── processed/            # Сгенерированные датасеты (в .gitignore)
├── src/
│   ├── generate_marian_data.py # Генератор синтетического корпуса EN-RU
│   ├── train_embeddings.py     # Пайплайн обучения эмбеддингов Moondream2
│   └── train_marian.py         # Скрипт дообучения MarianMT
├── outputs/                  # Сохраненные чекпоинты (в .gitignore)
└── run.py                    # Единый CLI-диспетчер запуска обучения
```