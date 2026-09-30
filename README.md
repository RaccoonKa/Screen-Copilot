# ✦ Screen Copilot

Local, high-performance visual AI coding assistant for IDEs powered by Moondream2 and fine-tuned MarianMT.

---

## EN version:

Screen Copilot is an autonomous screen overlay for developers. It captures a selected area of the screen in the IDE, uses computer vision to localize syntax errors, analyzes context with a local neural network, and lets you copy or paste a ready-made fix directly into the editor in one click.

---

## ⚡ Features

* **Fully offline and private:** All computations are performed locally on the GPU via PyTorch and CUDA, with no code sent to external cloud APIs.
* **Hybrid capture (HUD):** Select a code area using a rectangle (Rect) or a freeform contour (Lasso) with hardware acceleration on PyQt6.
* **Computer Vision Localization:** Automatic detection of red syntax error underlines in the IDE with a neon bounding box displayed over the code.
* **Bilingual technical translator:** A fine-tuned Seq2Seq `MarianMT` model for translating technical responses without breaking syntax or variable names.
* **Native Hot-Fix Injection:** Emulates pasting the corrected code block into the active IDE window via Win32 API system calls, regardless of keyboard layout.

---

## 🛠 Tech Stack

* **GUI:** PyQt6, Win32 API (ctypes)
* **Vision-Language Model:** Moondream2 (1.8B VLM)
* **Translation Engine:** Fine-tuned Helsinki-NLP/opus-mt-en-ru (MarianMT)
* **ML / DL:** PyTorch (bfloat16 / float16), Transformers, Hugging Face
* **Input & Capture:** Pynput, Pillow

---

## 🎮 Controls

* **`Alt + A`** — Activate the on-screen capture overlay
* **`R` / `L`** — Toggle modes: Rectangular area / Lasso
* **`Esc`** — Hide the overlay / close the result card
* **`Enter`** — Send a follow-up question about the code to the card's input field
* **`⚡ Paste in IDE`** — Transfer focus to the editor window and automatically apply the fix

---

## 📦 Building the Standalone Binary

Build the standalone version with PyInstaller:
pyinstaller build.spec --clean --noconfirm

The finished application will be available in the `dist/ScreenCopilot/` directory.

---

## RU версия:

Screen Copilot — это автономный экранный оверлей для разработчиков. Он перехватывает выделенную область экрана в IDE, с помощью компьютерного зрения локализует синтаксические ошибки, анализирует контекст локальной нейросетью и позволяет в один клик скопировать или вставить готовый фикс прямо в редактор.

---

## ⚡ Особенности

* **Полный офлайн и приватность:** Все вычисления производятся локально на GPU через PyTorch и CUDA без передачи кода во внешние облачные API.
* **Гибридный захват (HUD):** Выделение области кода через рамку (Rect) или произвольный контур (Lasso) с аппаратным ускорением на PyQt6.
* **Computer Vision Localization:** Автоматическое обнаружение красных подчеркиваний синтаксических ошибок в IDE с отображением неонового bounding box поверх кода.
* **Двуязычный технический переводчик:** Дообученная Seq2Seq модель `MarianMT` для перевода технических ответов без повреждения синтаксиса и названий переменных.
* **Native Hot-Fix Injection:** Эмуляция вставки исправленного блока кода в активное окно IDE через системные вызовы Win32 API независимо от раскладки.

---

## 🛠 Стек технологий

* **GUI:** PyQt6, Win32 API (ctypes)
* **Vision-Language Model:** Moondream2 (1.8B VLM)
* **Translation Engine:** Fine-tuned Helsinki-NLP/opus-mt-en-ru (MarianMT)
* **ML / DL:** PyTorch (bfloat16 / float16), Transformers, Hugging Face
* **Input & Capture:** Pynput, Pillow

---

## 🎮 Управление

* **`Alt + A`** — Активировать экранный оверлей захвата
* **`R` / `L`** — Переключение режимов: Прямоугольная область / Лассо
* **`Esc`** — Скрыть оверлей / закрыть карточку результата
* **`Enter`** — Отправить уточняющий вопрос по коду в инпут карточки
* **`⚡ Paste in IDE`** — Передать фокус в окно редактора и автоматически применить фикс

---

## 📦 Сборка автономного бинарника

Сборка standalone-версии с помощью PyInstaller:
pyinstaller build.spec --clean --noconfirm

Готовое приложение будет доступно в каталоге `dist/ScreenCopilot/`.