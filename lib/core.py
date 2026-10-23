#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageEnhance, ImageDraw, ImageFont, ImageOps
import sys
import os
import time
import shutil
import json

import base64
import hashlib
import platform
import secrets
from datetime import datetime, timezone
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization


ROOT = Path(__file__).resolve().parent.parent

# Folder foto bersama Android, mengikuti pola tools AFKAR lainnya.
_STORAGE_DL = Path.home() / "storage" / "downloads"
STORAGE_ROOT = (
    _STORAGE_DL / "afkar-photo-editor-pro"
    if _STORAGE_DL.is_dir()
    else ROOT
)
INPUT = STORAGE_ROOT / "input"
OUTPUT = STORAGE_ROOT / "output"
DEFAULT_USER = "TEMAN"
USER_FILE = ROOT / "user.json"
EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}

R = "\033[91m"
G = "\033[92m"
Y = "\033[93m"
B = "\033[94m"
M = "\033[95m"
C = "\033[96m"
W = "\033[97m"
DIM = "\033[90m"
RESET = "\033[0m"
BOLD = "\033[1m"


# Font ANSI Shadow — disamakan dengan autodownloadyoutube
FONT = {
    "R": ["██████╗ ", "██╔══██╗", "██████╔╝", "██╔══██╗", "██║  ██║", "╚═╝  ╚═╝"],
    "E": ["███████╗", "██╔════╝", "█████╗  ", "██╔══╝  ", "███████╗", "╚══════╝"],
    "N": ["███╗   ██╗", "████╗  ██║", "██╔██╗ ██║", "██║╚██╗██║", "██║ ╚████║", "╚═╝  ╚═══╝"],
    "D": ["██████╗ ", "██╔══██╗", "██║  ██║", "██║  ██║", "██████╔╝", "╚═════╝ "],
    "I": ["██╗", "██║", "██║", "██║", "██║", "╚═╝"],
    "A": [" █████╗ ", "██╔══██╗", "███████║", "██╔══██║", "██║  ██║", "╚═╝  ╚═╝"],
    "F": ["███████╗", "██╔════╝", "█████╗  ", "██╔══╝  ", "██║     ", "╚═╝     "],
    "K": ["██╗  ██╗", "██║ ██╔╝", "█████╔╝ ", "██╔═██╗ ", "██║  ██╗", "╚═╝  ╚═╝"],
}

def build_word(word):
    return ["".join(FONT[ch][r] for ch in word) for r in range(6)]

def banner(animated=False):
    os.system("clear")

    # Bingkai dihitung berdasarkan panjang karakter banner.
    width = 60
    inner = width - 2

    def framed(content=""):
        # Hilangkan kode warna ANSI saat menghitung panjang teks.
        import re
        plain = re.sub(r"\033\[[0-9;]*m", "", content)
        padding = max(0, inner - len(plain))
        left = padding // 2
        right = padding - left
        return (
            C + BOLD + "║" + RESET
            + " " * left + content + " " * right
            + C + BOLD + "║" + RESET
        )

    lines = [C + BOLD + "╔" + "═" * inner + "╗" + RESET]
    lines.append(framed())

    for row in build_word("RENDI"):
        lines.append(framed(C + BOLD + row + RESET))

    lines.append(framed())

    for row in build_word("AFKAR"):
        lines.append(framed(M + BOLD + row + RESET))

    lines.append(framed())
    lines.append(framed(G + BOLD + "AFKAR PHOTO EDITOR PRO" + RESET))
    lines.append(framed(Y + "TERMUX EDITION | BY AFKAR" + RESET))
    lines.append(framed(DIM + "BATCH PHOTO PROCESSING SYSTEM" + RESET))
    lines.append(C + BOLD + "╚" + "═" * inner + "╝" + RESET)

    for line in lines:
        print(line)
        if animated:
            time.sleep(0.07)

def load_user_name():
    try:
        data = json.loads(USER_FILE.read_text(encoding="utf-8"))
        return str(data.get("name", "")).strip()[:20]
    except (OSError, ValueError, TypeError, AttributeError):
        return ""


def save_user_name(name):
    try:
        USER_FILE.write_text(
            json.dumps({"name": name}, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        return True
    except OSError:
        return False


def show_welcome(name):
    message = "Selamat Datang"
    if name:
        message += ", " + name
    print()
    print(f"{BOLD}{Y}{message}!{RESET}")
    print(f"{G}Selamat menggunakan AFKAR PHOTO EDITOR PRO.{RESET}")
    time.sleep(0.8)


def introduce_user():
    print()
    print(f"{C}[AFKAR SETUP]{RESET}")
    print("Perkenalkan dirimu sebelum mulai menggunakan tool ini.")

    while True:
        try:
            name = input(f"{G}Nama kamu: {RESET}").strip()[:20]
        except (EOFError, KeyboardInterrupt):
            print()
            name = DEFAULT_USER
            break

        if name:
            break
        print(f"{Y}[!] Nama tidak boleh kosong.{RESET}")

    if save_user_name(name):
        print(f"{G}[+] Nama {name} berhasil disimpan.{RESET}")
    else:
        print(f"{Y}[!] Nama tidak tersimpan; sesi ini tetap berjalan.{RESET}")

    time.sleep(0.5)
    return name


def change_user_name():
    current_name = load_user_name() or DEFAULT_USER
    print(f"\\n{C}[GANTI NAMA PENGGUNA]{RESET}")
    print(f"Nama saat ini: {Y}{current_name}{RESET}")

    while True:
        try:
            new_name = input(
                f"{G}Masukkan nama baru (0 untuk batal): {RESET}"
            ).strip()[:20]
        except (EOFError, KeyboardInterrupt):
            print()
            return

        if new_name == "0":
            print(f"{Y}[!] Ganti nama dibatalkan.{RESET}")
            return

        if new_name:
            break
        print(f"{Y}[!] Nama tidak boleh kosong.{RESET}")

    if save_user_name(new_name):
        print(f"{G}[+] Nama berhasil diubah menjadi {new_name}.{RESET}")
    else:
        print(f"{R}[!] Nama gagal disimpan.{RESET}")

def photos():
    INPUT.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    return sorted(
        p for p in INPUT.iterdir()
        if p.is_file() and p.suffix.lower() in EXTS
    )

def ask_num(label, default, minimum=0, maximum=300):
    while True:
        raw = input(f"{C}{label}{RESET} [{default}]: ").strip()
        if not raw:
            return default
        try:
            value = float(raw)
            if minimum <= value <= maximum:
                return value
        except ValueError:
            pass
        print(R + f"Masukkan angka {minimum} sampai {maximum}." + RESET)

def progress(index, total, name, ok, failed):
    percent = int(index * 100 / total)
    filled = percent // 5
    bar = "█" * filled + "░" * (20 - filled)
    print(
        f"\r{G}[{bar}] {percent:3d}%{RESET} "
        f"{W}{index}/{total}{RESET} "
        f"{G}OK:{ok}{RESET} {R}Gagal:{failed}{RESET}",
        end="", flush=True
    )


def watermark(image, text, position="9", opacity=180, color="1"):
    if not text:
        return image

    colors = {
        "1": (255, 196, 0),    # Emas premium
        "2": (0, 235, 255),    # Cyan neon
        "3": (180, 70, 255),   # Ungu
        "4": (255, 55, 65),    # Merah
        "5": (130, 255, 0),    # Hijau lime
        "6": (30, 110, 255),   # Biru elektrik
        "7": (0, 0, 0),        # Hitam
        "8": (160, 160, 160),   # Abu-abu
        "9": (255, 255, 255),   # Putih
        "10": (255, 255, 0),    # Kuning cerah
    }

    rgb = colors.get(str(color), colors["1"])
    base = image.convert("RGBA")
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    size = max(16, min(base.size) // 28)

    try:
        font = ImageFont.truetype(
            "/system/fonts/Roboto-Regular.ttf", size
        )
    except OSError:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=2)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    margin = max(8, min(base.size) // 40)
    w, h = base.size

    positions = {
        "1": (margin, margin),
        "2": ((w-tw)//2, margin),
        "3": (w-tw-margin, margin),
        "4": (margin, (h-th)//2),
        "5": ((w-tw)//2, (h-th)//2),
        "6": (w-tw-margin, (h-th)//2),
        "7": (margin, h-th-margin),
        "8": ((w-tw)//2, h-th-margin),
        "9": (w-tw-margin, h-th-margin),
    }

    x, y = positions.get(str(position), positions["9"])
    x = max(0, min(x, max(0, w-tw)))
    y = max(0, min(y, max(0, h-th)))
    alpha = max(0, min(255, int(opacity)))

    # Outline gelap agar watermark lebih mudah dibaca.
    draw.text(
        (x, y), text, font=font,
        fill=(*rgb, alpha),
        stroke_width=max(1, size//16),
        stroke_fill=(0, 0, 0, alpha)
    )
    return Image.alpha_composite(base, overlay)


def choose_watermark_color():
    RESET = "[0m"
    GREEN = "[38;2;50;230;130m"
    RED = "[38;2;255;70;70m"

    colors = {
        "1": ("Emas premium", (255, 196, 0)),
        "2": ("Cyan neon", (0, 235, 255)),
        "3": ("Ungu", (180, 70, 255)),
        "4": ("Merah", (255, 55, 65)),
        "5": ("Hijau lime", (130, 255, 0)),
        "6": ("Biru elektrik", (30, 110, 255)),
        "7": ("Hitam", (110, 110, 110)),
        "8": ("Abu-abu", (160, 160, 160)),
        "9": ("Putih", (255, 255, 255)),
        "10": ("Kuning cerah", (255, 255, 0)),
    }

    def colored(text, rgb):
        r, g, b = rgb
        return f"[38;2;{r};{g};{b}m{text}{RESET}"

    print(f"[96mWarna watermark:{RESET}")
    for key, (label, rgb) in colors.items():
        print(colored(f"{key}. {label}", rgb))

    while True:
        choice = input(
            f"{GREEN}Pilih warna [1-10] (default 1 - Emas): {RESET}"
        ).strip() or "1"

        if choice in colors:
            label, rgb = colors[choice]
            print(colored(f"Warna dipilih: {label}", rgb))
            return choice

        print(f"{RED}Pilihan tidak valid.{RESET}")

def crop_image(image, ratio):
    ratios = {
        "1": (1, 1),
        "2": (4, 5),
        "3": (3, 4),
        "4": (9, 16),
        "5": (4, 3),
        "6": (16, 9),
    }
    if ratio not in ratios:
        return image

    rw, rh = ratios[ratio]
    w, h = image.size

    if w / h > rw / rh:
        nw = max(1, int(h * rw / rh))
        left = (w - nw) // 2
        return image.crop((left, 0, left + nw, h))

    nh = max(1, int(w * rh / rw))
    top = (h - nh) // 2
    return image.crop((0, top, w, top + nh))


def auto_enhance(image):
    from PIL import ImageStat

    has_alpha = "A" in image.getbands()
    alpha = image.getchannel("A") if has_alpha else None
    work = image.convert("RGB")

    work = ImageOps.autocontrast(work, cutoff=1)
    mean = ImageStat.Stat(work.convert("L")).mean[0]
    factor = 1.0 if mean <= 1 else max(0.88, min(1.12, 128 / mean))

    work = ImageEnhance.Brightness(work).enhance(factor)
    work = ImageEnhance.Color(work).enhance(1.08)
    work = ImageEnhance.Sharpness(work).enhance(1.12)

    if alpha is not None:
        work.putalpha(alpha)
    return work


def choose_crop():
    print("\033[96mCrop / rasio foto:\033[0m")
    print("\033[93m0. Tidak crop\033[0m")
    print("\033[95m1. Persegi 1:1\033[0m")
    print("\033[95m2. Portrait 4:5\033[0m")
    print("\033[95m3. Portrait 3:4\033[0m")
    print("\033[95m4. Portrait 9:16\033[0m")
    print("\033[95m5. Landscape 4:3\033[0m")
    print("\033[95m6. Landscape 16:9\033[0m")

    while True:
        choice = input("\033[92mPilih crop [0-6] (default 0): \033[0m").strip() or "0"
        if choice in ("0", "1", "2", "3", "4", "5", "6"):
            return None if choice == "0" else choice
        print("Pilihan tidak valid.")


def choose_watermark_position():
    RESET = "[0m"
    YELLOW = "[38;2;255;210;40m"
    GREEN = "[38;2;50;230;130m"
    RED = "[38;2;255;70;70m"

    positions = {
        "1": "Atas kiri",
        "2": "Atas tengah",
        "3": "Atas kanan",
        "4": "Tengah kiri",
        "5": "Tengah",
        "6": "Tengah kanan",
        "7": "Bawah kiri",
        "8": "Bawah tengah",
        "9": "Bawah kanan",
    }

    print(f"{YELLOW}Posisi watermark:{RESET}")
    for key, label in positions.items():
        print(f"{YELLOW}{key}. {label}{RESET}")

    while True:
        choice = input(
            f"{GREEN}Pilih posisi [1-9] (default 9): {RESET}"
        ).strip() or "9"

        if choice in positions:
            return choice

        print(f"{RED}Pilihan tidak valid.{RESET}")

def save_image(image, source, fmt="ORIGINAL", quality=92):
    if fmt == "ORIGINAL":
        fmt = source.suffix.lower().lstrip(".")
    fmt = fmt.lower()
    if fmt == "jpeg":
        fmt = "jpg"
    ext = ".jpg" if fmt == "jpg" else "." + fmt
    base_name = source.stem + "_EDITED"
    dest = OUTPUT / (base_name + ext)

    # Jangan timpa hasil edit sebelumnya.
    counter = 1
    while dest.exists():
        dest = OUTPUT / f"{base_name}_{counter:03d}{ext}"
        counter += 1

    if fmt in ("jpg", "webp"):
        image = image.convert("RGB")
    elif fmt == "png" and image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGBA")

    options = {}
    if fmt in ("jpg", "webp"):
        options["quality"] = int(quality)
    if fmt == "jpg":
        options["optimize"] = True
    image.save(dest, **options)
    return dest


def process_batch(mode):
    files = photos()
    if not files:
        print(R + "[!] Folder input kosong. Masukkan foto terlebih dahulu." + RESET)
        return

    print(f"\n{G}Ditemukan {len(files)} foto.{RESET}")
    print(Y + "Pengaturan diterapkan ke semua foto." + RESET)

    auto_mode = False
    brightness = contrast = saturation = sharpness = 1.0
    max_w = max_h = 0
    crop = None
    mark = ""
    position = "9"
    opacity = 180
    fmt = "ORIGINAL"
    quality = 92

    if mode == "edit":
        print("\n\033[96mMode peningkatan foto:\033[0m")
        print("\033[93m1. Auto Enhance\033[0m")
        print("\033[95m2. Manual\033[0m")
        choice = input("\033[92mPilih mode [1-2] (default 1): \033[0m").strip() or "1"

        if choice == "1":
            auto_mode = True
        elif choice == "2":
            brightness = ask_num("Brightness (1=normal)", 1.0, 0, 3)
            contrast = ask_num("Contrast (1=normal)", 1.0, 0, 3)
            saturation = ask_num("Saturation (1=normal)", 1.0, 0, 3)
            sharpness = ask_num("Sharpness (1=normal)", 1.0, 0, 3)
        else:
            print("Pilihan tidak valid.")
            return

        # Mode Edit tidak meminta batas ukuran.
        max_w = max_h = 0
        color = "1"
        crop = choose_crop()
        mark = input("\033[95mTeks watermark (kosong=lewati): \033[0m").strip()
        if mark:
            position = choose_watermark_position()
            color = choose_watermark_color()
            opacity = int(ask_num("Transparansi watermark (0-255)", 180, 0, 255))

    elif mode == "resize":
        max_w = int(ask_num("Batas lebar foto (pixel)", 1080, 1, 20000))
        max_h = int(ask_num("Batas tinggi foto (pixel)", 1080, 1, 20000))
        crop = choose_crop()

    elif mode == "watermark":
        mark = input("Teks watermark: ").strip()
        if not mark:
            print("Watermark kosong. Proses dibatalkan.")
            return
        position = choose_watermark_position()
        color = choose_watermark_color()
        opacity = int(ask_num("Transparansi watermark (0-255)", 180, 0, 255))

    elif mode == "convert":
        print("Format: 1 JPG | 2 PNG | 3 WEBP")
        choice = input("Pilih format [1-3]: ").strip()
        fmt = {"1": "jpg", "2": "png", "3": "webp"}.get(choice)
        if not fmt:
            print("Pilihan format tidak valid.")
            return
        if fmt in ("jpg", "webp"):
            quality = int(ask_num("Kualitas (1-100)", 92, 1, 100))
    else:
        print("Mode tidak dikenal.")
        return

    OUTPUT.mkdir(parents=True, exist_ok=True)
    ok = failed = 0
    print(f"\n{C}Memulai batch processing...{RESET}")

    for i, source in enumerate(files, 1):
        try:
            with Image.open(source) as original:
                image = ImageOps.exif_transpose(original).copy()

            if mode == "edit":
                if auto_mode:
                    image = auto_enhance(image)
                else:
                    image = ImageEnhance.Brightness(image).enhance(brightness)
                    image = ImageEnhance.Contrast(image).enhance(contrast)
                    image = ImageEnhance.Color(image).enhance(saturation)
                    image = ImageEnhance.Sharpness(image).enhance(sharpness)

            if mode in ("edit", "resize") and crop:
                image = crop_image(image, crop)

            if mode in ("edit", "resize") and (max_w or max_h):
                bound_w = max_w or image.width
                bound_h = max_h or image.height
                image.thumbnail(
                    (bound_w, bound_h), Image.Resampling.LANCZOS
                )

            if mode in ("edit", "watermark") and mark:
                image = watermark(image, mark, position, opacity, color)

            save_image(image, source, fmt, quality)
            ok += 1
            progress(i, len(files), source.name, ok, failed)
        except Exception as exc:
            failed += 1
            progress(i, len(files), source.name, ok, failed)
            print(f"\n{R}[!] {source.name}: {exc}{RESET}")

    print(f"\n\n{G}[SELESAI] Berhasil: {ok} | Gagal: {failed}{RESET}")
    print(f"{C}Hasil: {OUTPUT}{RESET}")

def photo_info():
    files = photos()
    if not files:
        print(Y + "Folder input belum berisi foto." + RESET)
        return
    for i, path in enumerate(files, 1):
        try:
            with Image.open(path) as im:
                print(
                    f"{G}{i:03d}.{RESET} {path.name} | "
                    f"{im.width}x{im.height} | {im.format} | "
                    f"{path.stat().st_size / 1024:.1f} KB"
                )
        except Exception as exc:
            print(R + f"{path.name}: {exc}" + RESET)

def open_folder(path):
    path.mkdir(parents=True, exist_ok=True)
    os.system("termux-open " + "'" + str(path).replace("'", "'\\''") + "' >/dev/null 2>&1")
    print(f"{C}Folder: {path}{RESET}")


# ============================================================
# AFKAR PHOTO EDITOR PRO - LICENSE
# ============================================================

PHOTO_APP_ID = "afkar-photo-editor-pro"
PHOTO_VALID_PLANS = {
    "1 Hari", "7 Hari", "1 Bulan", "1 Tahun", "Lifetime"
}
PHOTO_PRIVATE_DIR = Path.home() / ".afkar_photo_editor_license"
PHOTO_LICENSE_DIR = Path.home() / "storage" / "downloads" / "AFKAR_LISENSI"
PHOTO_LICENSE_FILE = PHOTO_LICENSE_DIR / "photo_editor_license.key"
PHOTO_MACHINE_FILE = PHOTO_PRIVATE_DIR / "machine.id"
PHOTO_PUBLIC_KEY_PEM = b'-----BEGIN PUBLIC KEY-----\nMCowBQYDK2VwAyEAI8COWafKSK7Jv6Vn6Ptrajn0ETOa5M5kbPnbeIH/4Vc=\n-----END PUBLIC KEY-----\n'


def photo_machine_id():
    PHOTO_PRIVATE_DIR.mkdir(parents=True, exist_ok=True)
    raw_id = ""
    try:
        raw_id = PHOTO_MACHINE_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        pass

    if not raw_id:
        raw_id = secrets.token_hex(16)
        PHOTO_MACHINE_FILE.write_text(raw_id, encoding="utf-8")
        try:
            PHOTO_MACHINE_FILE.chmod(0o600)
        except OSError:
            pass

    raw = f"{raw_id}|{platform.system()}|{platform.machine()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def photo_b64url_decode(value):
    if not isinstance(value, str) or not value:
        raise ValueError("Bagian Base64 kosong.")
    if not __import__("re").fullmatch(r"[A-Za-z0-9_-]+", value):
        raise ValueError("Format Base64 tidak valid.")
    decoded = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    if base64.urlsafe_b64encode(decoded).decode("ascii").rstrip("=") != value:
        raise ValueError("Base64 tidak canonical.")
    return decoded


def photo_parse_datetime(value):
    if not isinstance(value, str):
        raise ValueError("Tanggal tidak valid.")
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("Zona waktu tanggal tidak ada.")
    return dt.astimezone(timezone.utc)


def verify_photo_license_key(license_key):
    try:
        license_key = license_key.strip()
        if not license_key.startswith("AFKAR-"):
            return False, "Prefix lisensi tidak valid.", None

        parts = license_key[6:].split(".")
        if len(parts) != 2:
            return False, "Format lisensi tidak valid.", None

        payload_bytes = photo_b64url_decode(parts[0])
        signature = photo_b64url_decode(parts[1])
        if len(signature) != 64:
            return False, "Signature lisensi tidak valid.", None

        public_key = serialization.load_pem_public_key(PHOTO_PUBLIC_KEY_PEM)
        try:
            public_key.verify(signature, payload_bytes)
        except InvalidSignature:
            return False, "Signature lisensi tidak cocok.", None

        payload = json.loads(payload_bytes.decode("utf-8"))
        if not isinstance(payload, dict):
            return False, "Data lisensi tidak valid.", None

        required = (
            "app_id", "license_id", "plan",
            "machine_id", "created_at", "expires_at"
        )
        for field in required:
            if field not in payload:
                return False, f"Field lisensi hilang: {field}", None

        if payload["app_id"] != PHOTO_APP_ID:
            return False, "Lisensi bukan untuk Photo Editor Pro.", None

        if payload["machine_id"] != photo_machine_id():
            return False, "Machine ID tidak cocok dengan perangkat ini.", None

        plan = payload["plan"]
        if plan not in PHOTO_VALID_PLANS:
            return False, "Paket lisensi tidak valid.", None

        created_at = photo_parse_datetime(payload["created_at"])
        now = datetime.now(timezone.utc)
        if now < created_at:
            return False, "Waktu perangkat lebih awal dari tanggal lisensi.", None

        expires_raw = payload["expires_at"]
        if plan == "Lifetime":
            if expires_raw is not None:
                return False, "Lisensi Lifetime tidak boleh memiliki expired.", None
            expires_at = None
        else:
            if expires_raw is None:
                return False, "Tanggal expired tidak tersedia.", None
            expires_at = photo_parse_datetime(expires_raw)
            if expires_at <= created_at:
                return False, "Rentang tanggal lisensi tidak valid.", None
            if now >= expires_at:
                return False, "Lisensi sudah kedaluwarsa.", None

        return True, "Lisensi valid.", {
            "payload": payload,
            "expires_at": expires_at,
        }
    except Exception as exc:
        return False, f"Lisensi tidak valid: {exc}", None


PHOTO_LICENSE_INFO = None


def show_photo_license_details():
    global PHOTO_LICENSE_INFO

    key = ""
    try:
        key = PHOTO_LICENSE_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        pass

    if not key:
        print(R + "[X] BELUM AKTIF" + RESET)
        print("Machine ID:", photo_machine_id())
        print("Gunakan generator untuk membuat license key.")
        return

    valid, message, info = verify_photo_license_key(key)
    if not valid:
        PHOTO_LICENSE_INFO = None
        print(R + "[X] LICENSE TIDAK AKTIF" + RESET)
        print("Alasan:", message)
        print("Machine ID:", photo_machine_id())
        return

    PHOTO_LICENSE_INFO = info
    payload = info["payload"]
    expires = info["expires_at"]

    print()
    print("=" * 48)
    print("          DETAIL LICENSE")
    print("=" * 48)
    print("Status      : AKTIF")
    print("Produk      : AFKAR PHOTO EDITOR PRO")
    print("App ID      :", payload.get("app_id", "-"))
    print("Paket       :", payload.get("plan", "-"))
    print("License ID  :", payload.get("license_id", "-"))
    print("Dibuat      :", payload.get("created_at", "-"))
    print("Kedaluwarsa :", expires.strftime("%Y-%m-%d %H:%M UTC") if expires else "Lifetime / tidak terbatas")
    print("Machine ID  :", photo_machine_id())
    print("=" * 48)


def ensure_photo_license():
    PHOTO_LICENSE_DIR.mkdir(parents=True, exist_ok=True)
    machine_id = photo_machine_id()

    saved_key = ""
    try:
        saved_key = PHOTO_LICENSE_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        pass

    if saved_key:
        valid, message, info = verify_photo_license_key(saved_key)
        if valid:
            global PHOTO_LICENSE_INFO
            PHOTO_LICENSE_INFO = info
            payload = info["payload"]
            expires = info["expires_at"]
            expires_text = expires.strftime("%Y-%m-%d %H:%M UTC") if expires else "Tidak terbatas"
            print(f"LICENSE : AKTIF | {payload['plan']}")
            print(f"EXPIRED : {expires_text}")
            return True
        print(f"[!] Lisensi tersimpan tidak aktif: {message}")

    print()
    print(C + BOLD + "╔══════════════════════════════════════╗" + RESET)
    print(C + BOLD + "║" + RESET + Y + BOLD + "         AKTIVASI LICENSE             " + RESET + C + BOLD + "║" + RESET)
    print(C + BOLD + "╚══════════════════════════════════════╝" + RESET)
    print()
    print(B + BOLD + "Produk   : " + RESET + W + "AFKAR PHOTO EDITOR PRO" + RESET)
    print(B + BOLD + "Platform : " + RESET + W + "TERMUX EDITION" + RESET)
    print(B + BOLD + "Status   : " + RESET + Y + BOLD + "BELUM AKTIF" + RESET)
    print()
    print(M + BOLD + "Machine ID perangkat ini:" + RESET)
    print(G + BOLD + machine_id + RESET)
    print()
    print(C + "Pilih produk " + W + BOLD + "AFKAR PHOTO EDITOR PRO" + RESET + C + " di generator lisensi." + RESET)
    print(C + "Kirim Machine ID untuk meminta License Key." + RESET)
    print(Y + BOLD + "Hubungi : " + RESET + W + "rendiafkar.tools@gmail.com" + RESET)
    print(DIM + "Hubungi email tersebut untuk perpanjangan lisensi." + RESET)
    print()
    print(C + BOLD + "Tempel License Key " + RESET + DIM + "(kosong = batal):" + RESET)

    while True:
        try:
            key = input("License Key > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAktivasi dibatalkan.")
            return False

        if key == "0" or not key:
            print("Aplikasi ditutup karena belum diaktifkan.")
            return False

        valid, message, info = verify_photo_license_key(key)
        if not valid:
            print(f"[X] {message}")
            continue

        try:
            PHOTO_LICENSE_FILE.write_text(key, encoding="utf-8")
            try:
                PHOTO_LICENSE_FILE.chmod(0o600)
            except OSError:
                pass
        except OSError as exc:
            print(f"[X] Gagal menyimpan lisensi: {exc}")
            return False

        PHOTO_LICENSE_INFO = info
        print("[OK] Lisensi berhasil diverifikasi dan disimpan.")
        return True




def update_from_github():
    import subprocess

    root = Path(__file__).resolve().parent.parent

    def run_git(args):
        return subprocess.run(
            ["git"] + args,
            cwd=str(root),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
        )

    print("\n" + C + "Memeriksa pembaruan GitHub..." + RESET)
    try:
        check = run_git(["rev-parse", "--is-inside-work-tree"])
        if check.returncode != 0 or check.stdout.strip() != "true":
            print("Folder aplikasi bukan Git repository.")
            return

        remote = run_git(["remote", "get-url", "origin"])
        if remote.returncode != 0:
            print("Remote GitHub tidak ditemukan.")
            return

        url = remote.stdout.strip().lower().removesuffix(".git")
        if url not in (
            "https://github.com/rendi-afkar/afkar-photo-editor-pro",
            "git@github.com:rendi-afkar/afkar-photo-editor-pro",
            "ssh://git@github.com/rendi-afkar/afkar-photo-editor-pro",
        ):
            print("Update dibatalkan: remote bukan repository resmi.")
            return

        branch = run_git(["branch", "--show-current"])
        if branch.returncode != 0 or branch.stdout.strip() != "main":
            print("Update membutuhkan branch main.")
            return

        status = run_git(["status", "--porcelain"])
        if status.returncode != 0:
            print("Gagal memeriksa status file lokal.")
            return
        if status.stdout.strip():
            print("Update dibatalkan: ada perubahan lokal.")
            print("Simpan atau selesaikan perubahan lokal terlebih dahulu.")
            return

        fetch = run_git(["fetch", "--quiet", "origin", "main"])
        if fetch.returncode != 0:
            print("Gagal menghubungi GitHub:")
            print(fetch.stderr.strip() or "Periksa koneksi internet dan Git.")
            return

        ancestor = run_git([
            "merge-base", "--is-ancestor", "HEAD", "origin/main"
        ])
        if ancestor.returncode == 1:
            print("Update dibatalkan: riwayat lokal berbeda dari GitHub.")
            print("Periksa repository secara manual sebelum melanjutkan.")
            return
        if ancestor.returncode != 0:
            print("Gagal membandingkan versi.")
            return

        count = run_git([
            "rev-list", "--count", "HEAD..origin/main"
        ])
        if count.returncode != 0:
            print("Gagal membaca versi GitHub.")
            return

        if count.stdout.strip() == "0":
            print(G + "[OK] AFKAR PHOTO EDITOR PRO sudah versi terbaru." + RESET)
            return

        print(Y + "[UPDATE] Pembaruan tersedia: " + count.stdout.strip() + " commit." + RESET)
        confirm = input("Unduh dan pasang pembaruan? [y/N]: ").strip().lower()
        if confirm not in ("y", "ya"):
            print(Y + "Update dibatalkan." + RESET)
            return

        pull = run_git(["pull", "--ff-only", "origin", "main"])
        if pull.returncode != 0:
            print("Update gagal:")
            print(pull.stderr.strip() or pull.stdout.strip())
            return

        print(pull.stdout.strip() or "Pembaruan berhasil.")
        print("Tutup aplikasi, lalu jalankan kembali: bash main")
        print(C + "File lisensi tetap terpisah dan tidak diubah." + RESET)

    except subprocess.TimeoutExpired:
        print("Waktu pemeriksaan habis. Coba lagi nanti.")
    except OSError as exc:
        print("Kesalahan updater:", exc)


def main():
    # Startup AFKAR: banner, sapaan, lalu pemeriksaan status.
    banner(animated=True)

    name = load_user_name()
    if not name:
        name = introduce_user()

    show_welcome(name)
    print()

    # SYSTEM
    print(G + "[+] SYSTEM  : ONLINE" + RESET)

    # NETWORK
    try:
        import socket
        with socket.create_connection(("1.1.1.1", 53), timeout=1.5):
            print(G + "[+] NETWORK : CONNECTED" + RESET)
    except OSError:
        print(Y + "[!] NETWORK : OFFLINE / TIDAK TERDETEKSI" + RESET)

    # PYTHON
    print(G + f"[+] PYTHON  : READY (v{sys.version.split()[0]})" + RESET)

    # FFMPEG
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        print(G + "[+] FFMPEG  : READY" + RESET)
    else:
        print(Y + "[!] FFMPEG  : NOT FOUND" + RESET)

    # PILLOW
    try:
        import PIL
        print(G + f"[+] PILLOW  : READY (v{PIL.__version__})" + RESET)
    except Exception:
        print(R + "[!] PILLOW  : NOT READY" + RESET)

    # Status lisensi sebelum masuk ke alur aktivasi yang sudah ada.
    license_key = ""
    try:
        license_key = PHOTO_LICENSE_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        pass

    if license_key:
        license_valid, _, license_info = verify_photo_license_key(license_key)
    else:
        license_valid, license_info = False, None

    if license_valid:
        plan = license_info["payload"].get("plan", "-")
        print(G + f"[+] LICENSE : AKTIF - {plan}" + RESET)
    else:
        print(Y + "[!] LICENSE : BELUM AKTIF / TIDAK VALID" + RESET)

    print()

    # Pertahankan sistem verifikasi dan penyimpanan lisensi yang asli.
    if not ensure_photo_license():
        return

    INPUT.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)

    while True:
        banner()
        active_name = load_user_name() or name or DEFAULT_USER

        print(f"{Y}PENGGUNA: {active_name}{RESET}")
        print(G + "[+] SYSTEM  : ONLINE" + RESET)
        print(G + f"[+] PYTHON  : READY (v{sys.version.split()[0]})" + RESET)
        try:
            import PIL
            print(G + f"[+] PILLOW  : READY (v{PIL.__version__})" + RESET)
        except Exception:
            print(R + "[+] PILLOW  : NOT READY" + RESET)

        license_key = ""
        try:
            license_key = PHOTO_LICENSE_FILE.read_text(encoding="utf-8").strip()
        except OSError:
            pass

        license_valid, license_message, license_info = (
            verify_photo_license_key(license_key)
            if license_key else (False, "Belum diaktivasi.", None)
        )
        if license_valid:
            plan_name = license_info["payload"].get("plan", "-")
            print(G + f"[+] LICENSE : AKTIF - {plan_name}" + RESET)
        else:
            print(R + "[+] LICENSE : TIDAK AKTIF" + RESET)

        print(f"{W}INPUT : {INPUT}{RESET}")
        print(f"{W}OUTPUT: {OUTPUT}{RESET}")
        print()
        print(G + "[1] BATCH EDIT SEMUA FOTO" + RESET)
        print(G + "[2] RESIZE BATCH" + RESET)
        print(G + "[3] WATERMARK BATCH" + RESET)
        print(G + "[4] KONVERSI FORMAT BATCH" + RESET)
        print(G + "[5] INFO FOTO DI INPUT" + RESET)
        print(G + "[6] BUKA FOLDER INPUT" + RESET)
        print(G + "[7] BUKA FOLDER OUTPUT" + RESET)
        print(G + "[8] GANTI NAMA PENGGUNA" + RESET)
        print(G + "[9] LICENSE - AKTIVASI / CEK DETAIL" + RESET)
        print(G + "[10] UPDATE AFKAR PHOTO EDITOR PRO" + RESET)
        print(R + "[0] KELUAR" + RESET)

        choice = input(
            f"\n{Y}{active_name} > {RESET}"
        ).strip()

        if choice == "1":
            process_batch("edit")
        elif choice == "2":
            process_batch("resize")
        elif choice == "3":
            process_batch("watermark")
        elif choice == "4":
            process_batch("convert")
        elif choice == "5":
            photo_info()
        elif choice == "6":
            open_folder(INPUT)
        elif choice == "7":
            open_folder(OUTPUT)
        elif choice == "8":
            change_user_name()
        elif choice == "9":
            show_photo_license_details()
        elif choice == "10":
            update_from_github()
        elif choice == "0":
            print(
                G + f"Terima kasih, {active_name}, "
                "telah menggunakan AFKAR PHOTO EDITOR PRO!" + RESET
            )
            break
        else:
            print(R + "Pilihan tidak valid." + RESET)

        input(f"\n{DIM}Tekan ENTER untuk kembali ke menu...{RESET}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n" + Y + "Proses dihentikan." + RESET)
        sys.exit(0)
