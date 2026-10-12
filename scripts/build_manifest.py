import hashlib
import json
import os
from PIL import Image

def get_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def detect_transparency(img):
    if img.mode in ("RGBA", "LA"):
        alpha = img.getchannel("A")
        min_alpha, _ = alpha.getextrema()
        return min_alpha < 255
    return False

def get_human_label(filename):
    stem = os.path.splitext(filename)[0]
    custom_labels = {
        "cheerful-sunflower-mascot-badge": "Circular DP (Sunflower Mascot Badge)",
        "t-3-by-4-flower-mascot-guide": "3/4 View Flower Mascot (Official Character View)",
        "sanjivani-good-job": "Sanjivani Good Job",
        "sanjivani-goood-job": "Sanjivani Goood Job",
        "sanjivani-pmjjby": "Sanjivani PMJJBY",
        "sanjivani-pmsby": "Sanjivani PMSBY",
        "sanjivani-apy": "Sanjivani APY",
        "app-icon-1024": "App Icon",
        "sanjivani-original-colours": "Mascot — Original Colours (Embedded Raster)",
        "sanjivani-outline": "Mascot Outline (Single-Colour Vector)",
    }
    if stem in custom_labels:
        return custom_labels[stem]

    words = stem.replace("-", " ").replace("_", " ").split()
    capitalized = [w.capitalize() if not w.isupper() else w for w in words]
    return " ".join(capitalized)

def get_flag(filename):
    stem = os.path.splitext(filename)[0]
    flags = {
        "sanjivani-original-colours": "SVG (embedded raster). Not a scalable vector; contains an embedded base64 PNG.",
        "sanjivani-outline": "SVG, single-colour outline (297 paths, 400x600 pt).",
        "app-icon-1024": "Actual dimensions: 1254x1254 px, RGB (opaque).",
        "cheerful-sunflower-mascot-badge": "Circular DP asset (1254x1254 px, RGB, opaque).",
        "sanjivani-green-brand-colour": "Swatch image 2048x2048. Authoritative HEX: #0D6B3A.",
        "sanjivani-orange-brand-colour": "Swatch image 2048x2048. Authoritative HEX: #FF6A00.",
    }
    return flags.get(stem, "")

def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    orig_root = os.path.join(root, "assets", "original")
    manifest_path = os.path.join(root, "data", "manifest.json")
    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)

    categories = [
        "01-brand",
        "02-mascot",
        "03-icons",
        "04-stickers",
        "05-banners",
        "06-web-ui",
        "07-vector",
    ]

    category_titles = {
        "01-brand": "Brand Identity",
        "02-mascot": "Master Character Views",
        "03-icons": "Profile & App Icons",
        "04-stickers": "Stickers & Campaign Artwork",
        "05-banners": "Social Media Banners",
        "06-web-ui": "Web & UI Elements",
        "07-vector": "Scalable Vector Artwork",
    }

    manifest_files = []

    for cat in categories:
        cat_dir = os.path.join(orig_root, cat)
        if not os.path.exists(cat_dir):
            continue

        filenames = sorted(os.listdir(cat_dir))
        for filename in filenames:
            stem, ext = os.path.splitext(filename)
            filepath = os.path.join(cat_dir, filename)
            rel_path = f"assets/original/{cat}/{filename}"
            size_bytes = os.path.getsize(filepath)
            sha256 = get_sha256(filepath)
            ext_lower = ext.lower()

            if ext_lower == ".svg":
                fmt = "SVG"
                preview_path = rel_path
                transparency = True
                if stem == "sanjivani-outline":
                    width, height = 400, 600
                else:
                    width, height = 1024, 1536
            else:
                preview_rel = f"assets/web/{cat}/{stem}.webp"
                preview_path = preview_rel if os.path.exists(os.path.join(root, preview_rel.replace("/", os.sep))) else rel_path
                with Image.open(filepath) as img:
                    width, height = img.size
                    fmt = img.format or "PNG"
                    transparency = detect_transparency(img)

            entry = {
                "path": rel_path,
                "preview_path": preview_path,
                "category": cat,
                "category_title": category_titles.get(cat, cat),
                "filename": filename,
                "label": get_human_label(filename),
                "bytes": size_bytes,
                "sha256": sha256,
                "width": width,
                "height": height,
                "format": fmt,
                "transparency": transparency,
                "flag": get_flag(filename),
            }
            manifest_files.append(entry)

    manifest_data = {
        "generated_note": "Generated automatically from disk by scripts/build_manifest.py. Do not hand-edit.",
        "brand": {
            "name": "Sanjivani Vikas Foundation",
            "tagline": "PEOPLE | PARTNERSHIP | PROGRESS",
            "colours": [
                {"name": "Sanjivani Orange", "hex": "#FF6A00", "use": "Flower petals, emblem and accents"},
                {"name": "Sanjivani Green", "hex": "#0D6B3A", "use": "Jacket, wordmark, buttons and borders"},
                {"name": "Support Cream", "hex": "#FFF5E6", "use": "Light surfaces and supporting backgrounds"}
            ]
        },
        "total_files": len(manifest_files),
        "files": manifest_files
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    js_manifest_path = os.path.join(root, "data", "manifest.js")
    with open(js_manifest_path, "w", encoding="utf-8") as f:
        f.write("window.MANIFEST_DATA = " + json.dumps(manifest_data, indent=2) + ";\n")

    print(f"Successfully generated data/manifest.json and data/manifest.js with {len(manifest_files)} assets.")

if __name__ == "__main__":
    main()
