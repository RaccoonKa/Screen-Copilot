import sys
import yaml
from pathlib import Path
from src.train_embeddings import train_embeddings
from src.train_marian import train_marian


def main():
    root_dir = Path(__file__).resolve().parent
    mode = sys.argv[1].lower() if len(sys.argv) > 1 else "embeddings"

    if mode in ["marian", "translate", "trans"]:
        config_path = root_dir / "configs" / "marian.yaml"
        print("Starting MarianMT Fine-Tuning")
        runner = train_marian
    else:
        config_path = root_dir / "configs" / "embeddings.yaml"
        print("Starting Token Embeddings Training")
        runner = train_embeddings

    if not config_path.exists():
        print(f"Error: Config not found at {config_path}")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    runner(config)


if __name__ == "__main__":
    main()