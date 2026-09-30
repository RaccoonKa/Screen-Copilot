import json
import random
from pathlib import Path

TEMPLATES = [
    ("The function {func} returns a {type} value.", "Функция {func} возвращает значение {type}."),
    ("Make sure to handle the {err} exception properly.", "Убедитесь, что исключение {err} обрабатывается правильно."),
    ("Initialize the {var} parameter before calling {func}.", "Инициализируйте параметр {var} перед вызовом {func}."),
    ("The method {func} takes {arg} and raises {err} on failure.", "Метод {func} принимает {arg} и вызывает {err} в случае ошибки."),
    ("Variable {var} must be of type {type}, not {wrong_type}.", "Переменная {var} должна иметь тип {type}, а не {wrong_type}."),
    ("Use {kw} inside the loop to avoid an infinite recursion.", "Используйте {kw} внутри цикла, чтобы избежать бесконечной рекурсии."),
    ("You should import {mod} and pass {var} to {func}.", "Вам следует импортировать {mod} и передать {var} в {func}."),
    ("The error occurred because {var} has no attribute {attr}.", "Ошибка произошла из-за того, что {var} не имеет атрибута {attr}."),
    ("To fix this, update the signature of {func} to accept *args and **kwargs.", "Чтобы исправить это, обновите сигнатуру {func}, чтобы она принимала *args и **kwargs."),
    ("Check if {var} is not None before accessing {attr}.", "Проверьте, что {var} не равен None, перед обращением к {attr}."),
    ("Here is the corrected code:\n```python\n{code}\n```", "Вот исправленный код:\n```python\n{code}\n```"),
    ("Change `{line}` to `{fixed_line}` to solve the issue.", "Измените `{line}` на `{fixed_line}`, чтобы решить проблему.")
]

FUNCS = ["load_model", "process_event", "get_user_id", "forward", "backward", "encode_image", "render_card", "step"]
TYPES = ["bool", "int", "float", "str", "dict", "list", "torch.Tensor", "Optional[str]"]
ERRS = ["IndexError", "TypeError", "AttributeError", "KeyError", "ZeroDivisionError", "ValueError", "RuntimeError"]
VARS = ["input_ids", "attention_mask", "self.model", "user_token", "batch_size", "learning_rate", "image_embeds"]
KEYWORDS = ["continue", "break", "return", "yield", "async", "await", "raise"]
MODULES = ["torch", "os", "sys", "shutil", "transformers", "PyQt6.QtCore"]
ATTRS = ["shape", "grad", "weight", "is_loaded", "data"]
SNIPPETS = [
    ("res = total / count", "res = total / count if count != 0 else 0"),
    ("arr[idx] = val", "if idx < len(arr):\n    arr[idx] = val"),
    ("print(data['id'])", "print(data.get('id', None))"),
    ("loss.backward()", "loss.backward()\noptimizer.step()")
]


def build_marian_dataset(output_path=None, samples_count=2500):
    if output_path is None:
        root_dir = Path(__file__).resolve().parent.parent
        output_path = root_dir / "data" / "processed" / "marian_train.jsonl"
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    records = []

    for _ in range(samples_count):
        template_en, template_ru = random.choice(TEMPLATES)
        snip = random.choice(SNIPPETS)
        t_type = random.choice(TYPES)
        w_type = random.choice([t for t in TYPES if t != t_type])

        kwargs = {
            "func": f"`{random.choice(FUNCS)}()`",
            "type": f"`{t_type}`",
            "wrong_type": f"`{w_type}`",
            "err": f"`{random.choice(ERRS)}`",
            "var": f"`{random.choice(VARS)}`",
            "kw": f"`{random.choice(KEYWORDS)}`",
            "mod": f"`{random.choice(MODULES)}`",
            "attr": f"`{random.choice(ATTRS)}`",
            "arg": f"`{random.choice(VARS)}`",
            "code": snip[1],
            "line": snip[0],
            "fixed_line": snip[1]
        }

        en_text = template_en.format(**kwargs)
        ru_text = template_ru.format(**kwargs)
        records.append({"en": en_text, "ru": ru_text})

    random.shuffle(records)

    with open(output_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    return len(records)


if __name__ == "__main__":
    count = build_marian_dataset()
    print(f"Marian dataset generated: {count} samples")