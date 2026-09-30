import os
import json
import random
from pathlib import Path
from datasets import load_dataset

SYNTHETIC_ERRORS = [
    ("IndexError: list index out of range", "arr = [1, 2, 3]\nprint(arr[5])", "arr = [1, 2, 3]\nif len(arr) > 5:\n    print(arr[5])"),
    ("TypeError: can only concatenate str (not 'int') to str", "msg = 'Count: ' + 10", "msg = f'Count: {10}'"),
    ("AttributeError: 'NoneType' object has no attribute 'shape'", "res = get_tensor()\nprint(res.shape)", "res = get_tensor()\nif res is not None:\n    print(res.shape)"),
    ("ZeroDivisionError: division by zero", "avg = total / count", "avg = total / count if count != 0 else 0"),
    ("KeyError: 'user_id'", "uid = data['user_id']", "uid = data.get('user_id', None)"),
    ("SyntaxError: expected ':'", "if x > 10\n    return True", "if x > 10:\n    return True"),
    ("NameError: name 'logger' is not defined", "logger.info('Started')", "import logging\nlogger = logging.getLogger(__name__)\nlogger.info('Started')")
]

def make_sample(code, error="", fix="", bbox=None):
    text = ""
    if bbox:
        text += f"<bbox>{bbox[0]} {bbox[1]} {bbox[2]} {bbox[3]}</bbox> "
    text += f"<code_start>\n{code.strip()}\n<code_end>"
    if error:
        text += f" <error_start>\n{error.strip()}\n<error_end>"
    if fix:
        text += f" <fix_start>\n{fix.strip()}\n<fix_end>"
    return text.strip()

def build_dataset(output_path=None, target_size=2000):
    if output_path is None:
        root_dir = Path(__file__).resolve().parent.parent
        output_path = root_dir / "data" / "processed" / "tokens_train.jsonl"
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    records = []

    for _ in range(500):
        err, bug_code, fix_code = random.choice(SYNTHETIC_ERRORS)
        x1 = random.randint(10, 200)
        y1 = random.randint(10, 300)
        x2 = x1 + random.randint(100, 400)
        y2 = y1 + random.randint(50, 200)
        sample = make_sample(bug_code, error=err, fix=fix_code, bbox=(x1, y1, x2, y2))
        records.append({"text": sample})

    try:
        ds = load_dataset("sahil2801/CodeAlpaca-20k", split="train")
        for item in ds:
            if len(records) >= target_size:
                break
            code = item.get("output", "")
            instruction = item.get("instruction", "")
            if len(code) > 20 and len(code) < 500:
                has_bbox = random.random() < 0.4
                bbox = (random.randint(0, 100), random.randint(0, 100), random.randint(200, 800), random.randint(200, 600)) if has_bbox else None
                sample = make_sample(code, error=instruction if "error" in instruction.lower() else "", fix="", bbox=bbox)
                records.append({"text": sample})
    except Exception:
        pass

    random.shuffle(records)

    with open(output_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    return len(records)

if __name__ == "__main__":
    count = build_dataset()
    print(f"Dataset generated: {count} samples")