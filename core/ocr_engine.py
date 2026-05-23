from typing import Optional

import cv2
import numpy as np
import pytesseract
from PIL import Image
from rapidocr_onnxruntime import RapidOCR

import config
from utils.logger import get_logger
from utils.text_cleaner import clean_text

logger = get_logger(__name__)


class OCREngine:
    def __init__(self):
        logger.info("Initializing OCR engine (RapidOCR + pytesseract)")
        self.rapid = RapidOCR()
        self.tesseract_config = config.TESSERACT_CONFIG
        logger.info("OCR engine ready")

    def _preprocess(self, image_path: str) -> np.ndarray:
        img = cv2.imread(image_path)
        if img is None:
            pil = Image.open(image_path).convert("RGB")
            img = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)

        # Adaptive threshold (better for uneven lighting)
        thresh = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 31, 10,
        )
        return thresh

    def _ocr_rapid(self, image_path: str) -> tuple[str, float]:
        try:
            result, _ = self.rapid(image_path)
            if not result:
                return "", 0.0
            lines = []
            confidences = []
            for item in result:
                # RapidOCR format: [box, text, confidence]
                if len(item) >= 3:
                    _, text, conf = item[0], item[1], item[2]
                    lines.append(text)
                    confidences.append(float(conf))
            text = "\n".join(lines)
            avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
            return text, avg_conf
        except Exception as e:
            logger.warning(f"RapidOCR failed on {image_path}: {e}")
            return "", 0.0

    def _ocr_tesseract(self, image_path: str, preprocessed: Optional[np.ndarray] = None) -> tuple[str, float]:
        try:
            if preprocessed is not None:
                pil = Image.fromarray(preprocessed)
            else:
                pil = Image.open(image_path)
            data = pytesseract.image_to_data(
                pil, config=self.tesseract_config, output_type=pytesseract.Output.DICT
            )
            words = []
            confs = []
            for i, w in enumerate(data["text"]):
                if w and w.strip():
                    words.append(w)
                    try:
                        c = float(data["conf"][i])
                        if c >= 0:
                            confs.append(c / 100.0)
                    except (ValueError, TypeError):
                        pass
            text = " ".join(words)
            avg_conf = sum(confs) / len(confs) if confs else 0.0
            return text, avg_conf
        except Exception as e:
            logger.warning(f"Tesseract failed on {image_path}: {e}")
            return "", 0.0

    def extract(self, image_path: str) -> dict:
        """
        Run both engines, return the better result.
        Returns: {"text": str, "confidence": float, "engine": str}
        """
        logger.info(f"OCR extract: {image_path}")

        # Try RapidOCR on raw image (better for handwriting)
        rapid_text, rapid_conf = self._ocr_rapid(image_path)

        # Try Tesseract on preprocessed image (better for clean printed text)
        try:
            preprocessed = self._preprocess(image_path)
        except Exception as e:
            logger.warning(f"Preprocess failed, using raw: {e}")
            preprocessed = None
        tess_text, tess_conf = self._ocr_tesseract(image_path, preprocessed)

        # Pick the one with more content AND reasonable confidence
        rapid_score = len(rapid_text.strip()) * max(rapid_conf, 0.1)
        tess_score = len(tess_text.strip()) * max(tess_conf, 0.1)

        if rapid_score >= tess_score:
            chosen_text, chosen_conf, engine = rapid_text, rapid_conf, "rapidocr"
        else:
            chosen_text, chosen_conf, engine = tess_text, tess_conf, "tesseract"

        cleaned = clean_text(chosen_text)
        logger.info(
            f"OCR done: engine={engine} conf={chosen_conf:.2f} chars={len(cleaned)}"
        )
        return {"text": cleaned, "confidence": chosen_conf, "engine": engine}


_engine: Optional[OCREngine] = None


def get_ocr_engine() -> OCREngine:
    global _engine
    if _engine is None:
        _engine = OCREngine()
    return _engine