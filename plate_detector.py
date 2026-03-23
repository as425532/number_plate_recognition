import re
from functools import lru_cache


PLATE_PATTERN = re.compile(r"^[A-Z0-9]{6,10}$")


def _normalize_plate_text(text):
    cleaned = re.sub(r"[^A-Za-z0-9]", "", text or "").upper()
    return cleaned


@lru_cache(maxsize=1)
def _get_reader():
    import easyocr

    return easyocr.Reader(["en"], gpu=False)


def _load_dependencies():
    import cv2

    return cv2


def _extract_candidates(gray, cv2):
    blurred = cv2.bilateralFilter(gray, 11, 17, 17)
    edged = cv2.Canny(blurred, 30, 200)

    contours, _ = cv2.findContours(edged, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:20]

    candidates = []

    for contour in contours:
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.018 * perimeter, True)

        if len(approx) != 4:
            continue

        x, y, w, h = cv2.boundingRect(approx)
        aspect_ratio = w / float(h)
        area = w * h

        if aspect_ratio < 2 or aspect_ratio > 6:
            continue

        if area < 1500:
            continue

        padding_x = max(int(w * 0.08), 5)
        padding_y = max(int(h * 0.20), 5)

        x1 = max(x - padding_x, 0)
        y1 = max(y - padding_y, 0)
        x2 = min(x + w + padding_x, gray.shape[1])
        y2 = min(y + h + padding_y, gray.shape[0])

        crop = gray[y1:y2, x1:x2]

        if crop.size == 0:
            continue

        candidates.append(crop)

    if not candidates:
        candidates.append(gray)

    return candidates


def _build_variants(image, cv2):
    resized = cv2.resize(image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    _, otsu = cv2.threshold(resized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    adaptive = cv2.adaptiveThreshold(
        resized,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        15,
    )

    return [resized, otsu, adaptive]


def _ocr_candidates(candidates, cv2):
    reader = _get_reader()
    best_text = "Plate not detected"
    best_confidence = 0.0

    for crop in candidates:
        for variant in _build_variants(crop, cv2):
            results = reader.readtext(
                variant,
                detail=1,
                paragraph=False,
                allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
            )

            for _, text, confidence in results:
                normalized = _normalize_plate_text(text)

                if not normalized:
                    continue

                score = float(confidence)

                if PLATE_PATTERN.match(normalized):
                    score += 0.2
                elif len(normalized) >= 5:
                    score += 0.05
                else:
                    continue

                if score > best_confidence:
                    best_text = normalized
                    best_confidence = min(score, 0.99)

    return best_text, round(best_confidence, 2)


def detect_plate_text(image_path):
    try:
        cv2 = _load_dependencies()
        _get_reader()
    except ImportError:
        return {
            "plate_text": "Install opencv-python and easyocr to enable detection",
            "confidence": 0.0,
        }

    image = cv2.imread(image_path)

    if image is None:
        return {"plate_text": "Image not found", "confidence": 0.0}

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    candidates = _extract_candidates(gray, cv2)
    plate_text, confidence = _ocr_candidates(candidates, cv2)

    return {
        "plate_text": plate_text,
        "confidence": confidence,
    }
