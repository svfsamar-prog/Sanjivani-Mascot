import os
from PIL import Image

def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    orig_root = os.path.join(root, "assets", "original")
    web_root = os.path.join(root, "assets", "web")

    converted = 0
    skipped = 0

    for dirpath, _, filenames in os.walk(orig_root):
        rel_dir = os.path.relpath(dirpath, orig_root)
        dest_dir = os.path.join(web_root, rel_dir)
        os.makedirs(dest_dir, exist_ok=True)

        for filename in filenames:
            stem, ext = os.path.splitext(filename)
            ext_lower = ext.lower()

            if ext_lower == ".svg":
                # SVGs are not converted to webp
                skipped += 1
                continue

            orig_filepath = os.path.join(dirpath, filename)
            dest_filepath = os.path.join(dest_dir, f"{stem}.webp")

            with Image.open(orig_filepath) as img:
                w, h = img.size
                if w > 1200:
                    new_w = 1200
                    new_h = int(round(h * (1200.0 / w)))
                    # Use Resampling.LANCZOS
                    resized_img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                else:
                    resized_img = img.copy()

                # Save webp with quality 82, preserving transparency / alpha
                resized_img.save(dest_filepath, "WEBP", quality=82, method=6)
                converted += 1

    print(f"Generated {converted} .webp previews in assets/web/ (skipped {skipped} SVG files).")

if __name__ == "__main__":
    main()
