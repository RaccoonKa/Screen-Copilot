import os
import re
import json
import shutil
from pathlib import Path
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModelForCausalLM
from transformers.modeling_attn_mask_utils import AttentionMaskConverter
from tqdm import tqdm

_orig_ignore_sdpa = AttentionMaskConverter._ignore_causal_mask_sdpa

@staticmethod
def _safe_ignore_sdpa(*args, **kwargs):
    kwargs.pop("is_training", None)
    return _orig_ignore_sdpa(*args, **kwargs)

AttentionMaskConverter._ignore_causal_mask_sdpa = _safe_ignore_sdpa


def prepare_dynamic_modules(model_dir):
    moondream_path = os.path.join(model_dir, "moondream.py")
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

    targets = [model_dir, cache_dir]
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

    if os.path.exists(model_dir):
        for fname in os.listdir(model_dir):
            if fname.endswith(".py"):
                src = os.path.join(model_dir, fname)
                dst = os.path.join(cache_dir, fname)
                try:
                    shutil.copy2(src, dst)
                except Exception:
                    pass


class TokenDataset(Dataset):
    def __init__(self, jsonl_path, tokenizer, max_length=256):
        self.samples = []
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)
                self.samples.append(data["text"])

        self.encodings = tokenizer(
            self.samples,
            truncation=True,
            padding="max_length",
            max_length=max_length,
            return_tensors="pt"
        )

        self.labels = self.encodings.input_ids.clone()
        pad_id = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else 50256
        self.labels[self.labels == pad_id] = -100

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        return {
            "input_ids": self.encodings.input_ids[idx],
            "attention_mask": self.encodings.attention_mask[idx],
            "labels": self.labels[idx]
        }


def train_embeddings(config):
    root_dir = Path(__file__).resolve().parent.parent
    dataset_path = root_dir / config["dataset_path"]
    output_dir = root_dir / config["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    cuda_ok = torch.cuda.is_available()
    device = "cuda" if cuda_ok else "cpu"
    print(f"--> Using device: {device.upper()}")
    if cuda_ok:
        print(f"--> GPU: {torch.cuda.get_device_name(0)}")

    model_path = config["model_path"]
    prepare_dynamic_modules(model_path)

    new_tokens = config["new_tokens"]

    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token or "<|endoftext|>"

    num_added = tokenizer.add_special_tokens({"additional_special_tokens": new_tokens})
    print(f"Added {num_added} new tokens to tokenizer vocabulary")

    dtype = torch.bfloat16 if (cuda_ok and torch.cuda.is_bf16_supported()) else torch.float32

    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        trust_remote_code=True,
        torch_dtype=dtype,
        local_files_only=True
    ).to(device)

    lm = model.text_model if hasattr(model, "text_model") else model
    lm.resize_token_embeddings(len(tokenizer))

    for param in model.parameters():
        param.requires_grad = False

    embedding_layer = lm.get_input_embeddings()
    embedding_layer.weight.requires_grad = True

    dataset = TokenDataset(dataset_path, tokenizer, max_length=config.get("max_length", 256))
    batch_size = config.get("batch_size", 8)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    lr = float(config.get("learning_rate", 1e-4))
    optimizer = torch.optim.AdamW([embedding_layer.weight], lr=lr, weight_decay=0.0)

    lm.train()
    epochs = config.get("epochs", 3)

    for epoch in range(epochs):
        total_loss = 0.0
        pbar = tqdm(dataloader, desc=f"Epoch {epoch + 1}/{epochs}")

        for batch in pbar:
            optimizer.zero_grad()

            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            outputs = lm(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
            loss = outputs.loss

            if torch.isnan(loss):
                continue

            loss.backward()

            with torch.no_grad():
                embedding_layer.weight.grad[:-num_added] = 0.0
                torch.nn.utils.clip_grad_norm_([embedding_layer.weight], max_norm=1.0)

            optimizer.step()

            total_loss += loss.item()
            pbar.set_postfix({"loss": f"{loss.item():.4f}"})

        avg_loss = total_loss / max(1, len(dataloader))
        print(f"Epoch {epoch + 1} finished. Avg Loss: {avg_loss:.4f}")

    tokenizer.save_pretrained(str(output_dir))
    model.save_pretrained(str(output_dir))
    print(f"Model and tokenizer successfully saved to {output_dir}")