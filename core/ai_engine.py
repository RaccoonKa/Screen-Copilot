import io
import os
import re
import shutil
import threading
from PIL import Image
from PyQt6 import QtCore, QtGui
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer


import logging
import warnings
from transformers.utils import logging as hf_logging

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*past_key_values.*")
hf_logging.set_verbosity_error()
logging.getLogger("transformers.tokenization_utils_base").setLevel(logging.ERROR)


from transformers.modeling_attn_mask_utils import AttentionMaskConverter
from core.translator import translator
from config import MODEL_DIR

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
warnings.filterwarnings("ignore")

_orig_ignore_sdpa = AttentionMaskConverter._ignore_causal_mask_sdpa

@staticmethod
def _safe_ignore_sdpa(*args, **kwargs):
    kwargs.pop("is_training", None)
    return _orig_ignore_sdpa(*args, **kwargs)

AttentionMaskConverter._ignore_causal_mask_sdpa = _safe_ignore_sdpa


def prepare_dynamic_modules():
    moondream_path = os.path.join(MODEL_DIR, "moondream.py")
    if os.path.exists(moondream_path):
        try:
            with open(moondream_path, "r", encoding="utf-8") as f:
                content = f.read()
            if "from .fourier_features import" not in content:
                content = "from .fourier_features import FourierFeatures\n" + content
                with open(moondream_path, "w", encoding="utf-8") as f:
                    f.write(content)
        except Exception:
            pass

    cache_dir = os.path.expanduser("~/.cache/huggingface/modules/transformers_modules/moondream2")
    os.makedirs(cache_dir, exist_ok=True)
    init_path = os.path.join(cache_dir, "__init__.py")
    if not os.path.exists(init_path):
        try:
            with open(init_path, "w", encoding="utf-8") as f:
                f.write("")
        except Exception:
            pass

    targets = [MODEL_DIR, cache_dir]
    for folder in targets:
        phi_path = os.path.join(folder, "modeling_phi.py")
        if os.path.exists(phi_path):
            try:
                with open(phi_path, "r", encoding="utf-8") as f:
                    content = f.read()
                new_content = re.sub(r",?\s*is_training\s*=\s*[^,\)]+", "", content)
                if new_content != content:
                    with open(phi_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
            except Exception:
                pass

    if os.path.exists(MODEL_DIR):
        for fname in os.listdir(MODEL_DIR):
            if fname.endswith(".py"):
                src = os.path.join(MODEL_DIR, fname)
                dst = os.path.join(cache_dir, fname)
                try:
                    shutil.copy2(src, dst)
                except Exception:
                    pass


def qimage_to_pil(qimage: QtGui.QImage) -> Image.Image:
    buffer = QtCore.QBuffer()
    buffer.open(QtCore.QIODevice.OpenModeFlag.ReadWrite)
    qimage.save(buffer, "PNG")
    data = bytes(buffer.data())
    return Image.open(io.BytesIO(data)).convert("RGB")


class TranslationWorker(QtCore.QThread):
    finished = QtCore.pyqtSignal(str)
    error_occurred = QtCore.pyqtSignal(str)

    def __init__(self, text: str):
        super().__init__()
        self.text = text

    def run(self):
        try:
            translated = translator.translate_en_to_ru(self.text)
            self.finished.emit(translated)
        except Exception as e:
            self.error_occurred.emit(str(e))


class AIInferenceWorker(QtCore.QThread):
    token_generated = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal(str)
    error_occurred = QtCore.pyqtSignal(str)
    status_changed = QtCore.pyqtSignal(str)

    def __init__(self, engine, pil_image: Image.Image = None, prompt: str = ""):
        super().__init__()
        self.engine = engine
        self.image = pil_image

        default_prompt = (
            "Find the error in this code and provide only the clean corrected Python code block:"
        )
        self.raw_prompt = prompt or default_prompt

    def run(self):
        try:
            if not self.engine.is_loaded:
                self.status_changed.emit("Loading the model into the GPU...")
                self.engine.load_model()

            prompt_en = self.raw_prompt
            if translator.is_cyrillic(self.raw_prompt):
                self.status_changed.emit("Translation of the request...")
                prompt_en = translator.translate_ru_to_en(self.raw_prompt)

            self.status_changed.emit("Screen analysis...")

            if self.image is not None:
                img = self.image
                if img.height < 220:
                    scale = int(220 / img.height) + 1
                    img = img.resize(
                        (img.width * scale, img.height * scale),
                        Image.Resampling.LANCZOS,
                    )

                image_embeds = self.engine.model.encode_image(img)
                self.engine.last_embeds = image_embeds
            else:
                image_embeds = self.engine.last_embeds

            if image_embeds is None:
                raise ValueError("First, select the area of the screen!")

            streamer = TextIteratorStreamer(
                self.engine.tokenizer, skip_special_tokens=True
            )

            gen_kwargs = {
                "image_embeds": image_embeds,
                "question": prompt_en,
                "tokenizer": self.engine.tokenizer,
                "streamer": streamer,
                "max_new_tokens": 384,
                "repetition_penalty": 1.05,
            }

            exc_holder = []
            res_holder = []

            def worker_target():
                try:
                    res = self.engine.model.answer_question(**gen_kwargs)
                    if res:
                        res_holder.append(res)
                except Exception as ex:
                    exc_holder.append(ex)
                    try:
                        streamer.end()
                    except Exception:
                        pass

            thread = threading.Thread(target=worker_target)
            thread.start()

            full_en_text = ""
            for text in streamer:
                full_en_text += text
                self.token_generated.emit(text)

            thread.join()

            if exc_holder:
                raise exc_holder[0]

            if not full_en_text.strip() and res_holder:
                direct_ans = str(res_holder[0]).strip()
                if direct_ans:
                    full_en_text = direct_ans
                    self.token_generated.emit(full_en_text)

            self.finished.emit(full_en_text)

        except Exception as e:
            import traceback

            traceback.print_exc()
            self.error_occurred.emit(f"{type(e).__name__}: {e}")


class AIEngine:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.is_loaded = False
        self.last_embeds = None

    def load_model(self):
        if self.is_loaded:
            return

        prepare_dynamic_modules()

        device = "cuda" if torch.cuda.is_available() else "cpu"
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32

        self.tokenizer = AutoTokenizer.from_pretrained(
            MODEL_DIR,
            local_files_only=True
        )

        self.model = AutoModelForCausalLM.from_pretrained(
            MODEL_DIR,
            trust_remote_code=True,
            torch_dtype=dtype,
            local_files_only=True
        ).to(device)

        self.is_loaded = True

    def create_worker(self, qimage: QtGui.QImage = None, prompt: str = "") -> AIInferenceWorker:
        pil_img = qimage_to_pil(qimage) if qimage is not None else None
        return AIInferenceWorker(self, pil_img, prompt)

    def create_translation_worker(self, text: str) -> TranslationWorker:
        return TranslationWorker(text)