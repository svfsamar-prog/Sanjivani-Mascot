import argparse
import hashlib
import json
import os
import re
import sys
from html.parser import HTMLParser

def get_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def verify_originals(root):
    inv_path = os.path.join(root, "asset-inventory.json")
    with open(inv_path, "r", encoding="utf-8") as f:
        inventory = json.load(f)

    files = inventory["files"]
    matches = 0
    naming_violations = 0

    for item in files:
        dst = os.path.join(root, item["dest_path"].replace("/", os.sep))
        rel_dst = item["dest_path"]

        # Check naming rule: lowercase, no spaces
        filename = os.path.basename(rel_dst)
        if any(c.isupper() for c in filename) or " " in filename:
            print(f"Naming violation: {filename}")
            naming_violations += 1

        if not os.path.exists(dst):
            print(f"File missing: {dst}")
            continue

        actual_sha = get_sha256(dst)
        if actual_sha == item["sha256"]:
            matches += 1
        else:
            print(f"Hash mismatch: {rel_dst} (expected {item['sha256']}, got {actual_sha})")

    print(f"{matches}/{len(files)} sha256 match")
    print(f"{naming_violations} files with spaces or uppercase in name")

    if matches != len(files) or naming_violations != 0:
        sys.exit(1)

def verify_manifest(root):
    manifest_path = os.path.join(root, "data", "manifest.json")
    if not os.path.exists(manifest_path):
        print(f"Manifest missing: {manifest_path}")
        sys.exit(1)

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Check every manifest file path exists
    manifest_files = manifest.get("files", [])
    missing_paths = 0
    manifest_dest_paths = set()

    for item in manifest_files:
        orig_path = os.path.join(root, item["path"].replace("/", os.sep))
        manifest_dest_paths.add(item["path"].replace("\\", "/"))
        if not os.path.exists(orig_path):
            print(f"Original path from manifest not found: {orig_path}")
            missing_paths += 1

        if "preview_path" in item and item["preview_path"]:
            prev_path = os.path.join(root, item["preview_path"].replace("/", os.sep))
            if not os.path.exists(prev_path):
                print(f"Preview path from manifest not found: {prev_path}")
                missing_paths += 1

    # Check every file in assets/original/ appears in manifest
    orig_dir = os.path.join(root, "assets", "original")
    files_on_disk = set()
    for dirpath, _, filenames in os.walk(orig_dir):
        for f in filenames:
            rel = os.path.relpath(os.path.join(dirpath, f), root).replace("\\", "/")
            files_on_disk.add(rel)

    missing_from_manifest = files_on_disk - manifest_dest_paths
    if missing_from_manifest:
        print(f"Files in assets/original/ missing from manifest: {missing_from_manifest}")
        sys.exit(1)

    if missing_paths > 0:
        print(f"{missing_paths} paths listed in manifest do not exist.")
        sys.exit(1)

    # Calculate total size of assets/web/
    web_dir = os.path.join(root, "assets", "web")
    total_web_bytes = 0
    if os.path.exists(web_dir):
        for dirpath, _, filenames in os.walk(web_dir):
            for f in filenames:
                total_web_bytes += os.path.getsize(os.path.join(dirpath, f))

    print(f"Manifest valid: {len(manifest_files)} items verified. Every file in assets/original/ appears in manifest.")
    print(f"Total size of assets/web/: {total_web_bytes:,} bytes ({total_web_bytes / (1024*1024):.2f} MB)")

class LinkExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        for k, v in attrs:
            if k in ("src", "href") and v:
                self.links.append((tag, k, v))

def verify_links(root):
    index_path = os.path.join(root, "index.html")
    if not os.path.exists(index_path):
        print(f"index.html not found: {index_path}")
        sys.exit(1)

    with open(index_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    parser = LinkExtractor()
    parser.feed(html_content)

    errors = 0
    for tag, attr, url in parser.links:
        # Ignore in-page anchors
        if url.startswith("#"):
            continue
        # External URLs not allowed
        if url.startswith("http://") or url.startswith("https://") or url.startswith("//"):
            print(f"External URL forbidden in {tag} {attr}: {url}")
            errors += 1
            continue
        # Absolute paths starting with / not allowed
        if url.startswith("/"):
            print(f"Absolute path forbidden in {tag} {attr}: {url}")
            errors += 1
            continue

        # Check local file existence
        # Strip query string or hash if present
        clean_url = url.split("?")[0].split("#")[0]
        local_path = os.path.join(root, clean_url.replace("/", os.sep))
        if not os.path.exists(local_path):
            print(f"Link target does not exist ({tag} {attr}='{url}'): {local_path}")
            errors += 1

    if errors == 0:
        print(f"All links ({len(parser.links)} total) in index.html verified: 0 broken, 0 absolute, 0 external.")
    else:
        print(f"Total link errors: {errors}")
        sys.exit(1)

def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parser = argparse.ArgumentParser()
    parser.add_argument("--originals", action="store_true", help="Verify original assets checksums and naming")
    parser.add_argument("--manifest", action="store_true", help="Verify data/manifest.json paths and consistency")
    parser.add_argument("--links", action="store_true", help="Verify relative links in index.html")
    args = parser.parse_args()

    if args.originals:
        verify_originals(root)
    elif args.manifest:
        verify_manifest(root)
    elif args.links:
        verify_links(root)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
