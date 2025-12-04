import json
from pathlib import Path

class ManifestLoader:
    def __init__(self, manifest_path: str):
        self.path = Path(manifest_path)

    def load(self):
        with self.path.open("r", encoding="utf-8") as f:
            return json.load(f)