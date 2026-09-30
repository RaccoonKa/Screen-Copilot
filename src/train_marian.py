import json
from pathlib import Path
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from tqdm import tqdm


class Seq2SeqDataset(Dataset):
    def __init__(self, jsonl_path, tokenizer, max_length=128):
        self.en_texts = []
        self.ru_texts = []

        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                item = json.loads(line)
                self.en_texts.append(item["en"])
                self.ru_texts.append(item["ru"])

        self.model_inputs = tokenizer(
            self.en_texts,
            truncation=True,
            padding="max_length",
            max_length=max_length,
            return_tensors="pt"
        )

        with tokenizer.as_target_tokenizer():
            labels = tokenizer(
                self.ru_texts,
                truncation=True,
                padding="max_length",
                max_length=max_length,
                return_tensors="pt"
            )

        self.labels = labels.input_ids
        pad_id = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else 65000
        self.labels[self.labels == pad_id] = -100

    def __len__(self):
        return len(self.en_texts)

    def __getitem__(self, idx):
        return {
            "input_ids": self.model_inputs.input_ids[idx],
            "attention_mask": self.model_inputs.attention_mask[idx],
            "labels": self.labels[idx]
        }


def train_marian(config):
    root_dir = Path(__file__).resolve().parent.parent
    dataset_path = root_dir / config["dataset_path"]
    output_dir = root_dir / config["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    cuda_ok = torch.cuda.is_available()
    device = "cuda" if cuda_ok else "cpu"
    print(f"--> Using device: {device.upper()}")
    if cuda_ok:
        print(f"--> GPU: {torch.cuda.get_device_name(0)}")

    model_name = config["model_name"]
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    dtype = torch.bfloat16 if (cuda_ok and torch.cuda.is_bf16_supported()) else torch.float32

    model = AutoModelForSeq2SeqLM.from_pretrained(
        model_name,
        torch_dtype=dtype
    ).to(device)

    dataset = Seq2SeqDataset(dataset_path, tokenizer, max_length=config.get("max_length", 128))
    batch_size = config.get("batch_size", 16)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    optimizer = torch.optim.AdamW(model.parameters(), lr=float(config.get("learning_rate", 5e-5)))

    model.train()
    epochs = config.get("epochs", 3)

    for epoch in range(epochs):
        total_loss = 0.0
        pbar = tqdm(dataloader, desc=f"Epoch {epoch + 1}/{epochs}")

        for batch in pbar:
            optimizer.zero_grad()

            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels
            )

            loss = outputs.loss
            loss.backward()

            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

            total_loss += loss.item()
            pbar.set_postfix({"loss": f"{loss.item():.4f}"})

        avg_loss = total_loss / max(1, len(dataloader))
        print(f"Epoch {epoch + 1} finished. Avg Loss: {avg_loss:.4f}")

    tokenizer.save_pretrained(str(output_dir))
    model.save_pretrained(str(output_dir))
    print(f"Marian model and tokenizer saved to {output_dir}")