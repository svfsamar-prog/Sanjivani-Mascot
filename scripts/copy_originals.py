import json
import os
import shutil
import hashlib

def get_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    inv_path = os.path.join(root, "asset-inventory.json")

    with open(inv_path, "r", encoding="utf-8") as f:
        inventory = json.load(f)

    files = inventory["files"]
    print(f"Copying {len(files)} original asset files...")

    copied = 0
    for item in files:
        src = os.path.join(root, item["source_path"].replace("/", os.sep))
        dst = os.path.join(root, item["dest_path"].replace("/", os.sep))

        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)

        dst_sha = get_sha256(dst)
        expected_sha = item["sha256"]
        if dst_sha != expected_sha:
            raise ValueError(f"Checksum mismatch for {dst}: got {dst_sha}, expected {expected_sha}")
        copied += 1

    print(f"Successfully copied and verified {copied}/{len(files)} original files.")

if __name__ == "__main__":
    main()
