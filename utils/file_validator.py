import os
import re
from pathlib import Path
from typing import Optional

import config


class FileValidationError(Exception):
    pass


def get_extension(filename: str) -> str:
    return Path(filename).suffix.lower().lstrip(".")


def is_allowed_extension(filename: str) -> bool:
    return get_extension(filename) in config.ALLOWED_EXTENSIONS


def is_image(filename: str) -> bool:
    return get_extension(filename) in {"jpg", "jpeg", "png", "bmp", "tiff"}


def is_pdf(filename: str) -> bool:
    return get_extension(filename) == "pdf"


def is_docx(filename: str) -> bool:
    return get_extension(filename) == "docx"


def is_txt(filename: str) -> bool:
    return get_extension(filename) == "txt"


def validate_size(filepath: str) -> None:
    size = os.path.getsize(filepath)
    if size == 0:
        raise FileValidationError("File is empty")
    if size > config.MAX_FILE_SIZE_BYTES:
        raise FileValidationError(
            f"File size {size / 1024 / 1024:.2f} MB exceeds limit "
            f"{config.MAX_FILE_SIZE_MB} MB"
        )


def validate_file(filepath: str, original_filename: Optional[str] = None) -> dict:
    if not os.path.exists(filepath):
        raise FileValidationError(f"File not found: {filepath}")

    name = original_filename or os.path.basename(filepath)

    if not is_allowed_extension(name):
        raise FileValidationError(
            f"Extension not allowed. Got: '{get_extension(name)}'. "
            f"Allowed: {sorted(config.ALLOWED_EXTENSIONS)}"
        )

    validate_size(filepath)

    return {
        "filename": name,
        "extension": get_extension(name),
        "size_bytes": os.path.getsize(filepath),
        "is_image": is_image(name),
        "is_pdf": is_pdf(name),
        "is_docx": is_docx(name),
        "is_txt": is_txt(name),
    }


def sanitize_filename(filename: str) -> str:
    name = os.path.basename(filename)
    name = re.sub(r"[^\w\s.\-]", "_", name)
    name = re.sub(r"\s+", "_", name)
    name = name.strip("_.")
    return name or "unnamed"