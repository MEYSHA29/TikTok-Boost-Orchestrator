"""
TikTok Boost Orchestrator - CAPTCHA Solving Pipeline
Multi-backend CAPTCHA solver: OCR, 2captcha, Anti-Captcha, manual fallback.
"""

import base64
import io
import os
import tempfile
from typing import Optional

import pytesseract
from PIL import Image, ImageFilter, ImageEnhance
from loguru import logger


class CaptchaSolver:
    """Unified CAPTCHA solving interface."""

    def __init__(
        self,
        solver_type: str = "ocr",
        api_key_2captcha: str = "",
        api_key_anticaptcha: str = "",
    ):
        self.solver_type = solver_type
        self.api_key_2captcha = api_key_2captcha
        self.api_key_anticaptcha = api_key_anticaptcha

        # Initialize paid solvers if keys provided
        self._2captcha = None
        self._anticaptcha = None

        if api_key_2captcha:
            try:
                from twocaptcha import TwoCaptcha
                self._2captcha = TwoCaptcha(api_key_2captcha)
            except ImportError:
                logger.warning("2captcha package not installed. Install: pip install 2captcha-python")

        if api_key_anticaptcha:
            try:
                from anticaptchaofficial.imagecaptcha import imagecaptcha
                self._anticaptcha = imagecaptcha()
                self._anticaptcha.set_key(api_key_anticaptcha)
            except ImportError:
                logger.warning("anticaptchaofficial package not installed.")

    def solve_image_text(self, image_bytes: bytes) -> Optional[str]:
        """Solve image-based text CAPTCHA using OCR or paid services."""
        if self.solver_type == "ocr":
            return self._solve_ocr(image_bytes)
        elif self.solver_type == "2captcha" and self._2captcha:
            return self._solve_2captcha(image_bytes)
        elif self.solver_type == "anticaptcha" and self._anticaptcha:
            return self._solve_anticaptcha(image_bytes)
        elif self.solver_type == "manual":
            return self._solve_manual(image_bytes)
        else:
            logger.warning(f"Unknown solver type: {self.solver_type}, falling back to OCR")
            return self._solve_ocr(image_bytes)

    def solve_recaptcha(self, site_key: str, page_url: str) -> Optional[str]:
        """Solve reCAPTCHA v2 using paid service."""
        if self._2captcha:
            try:
                result = self._2captcha.recaptcha(sitekey=site_key, url=page_url)
                return result.get("code") if isinstance(result, dict) else str(result)
            except Exception as e:
                logger.error(f"2captcha reCAPTCHA failed: {e}")
        if self._anticaptcha:
            try:
                from anticaptchaofficial.recaptchav2proxyless import recaptchaV2Proxyless
                solver = recaptchaV2Proxyless()
                solver.set_key(self.api_key_anticaptcha)
                solver.set_website_url(page_url)
                solver.set_website_key(site_key)
                return solver.solve_and_return_solution()
            except Exception as e:
                logger.error(f"Anti-captcha reCAPTCHA failed: {e}")
        logger.error("No reCAPTCHA solver available")
        return None

    def solve_hcaptcha(self, site_key: str, page_url: str) -> Optional[str]:
        """Solve hCaptcha using paid service."""
        if self._2captcha:
            try:
                result = self._2captcha.hcaptcha(sitekey=site_key, url=page_url)
                return result.get("code") if isinstance(result, dict) else str(result)
            except Exception as e:
                logger.error(f"2captcha hCaptcha failed: {e}")
        logger.error("No hCaptcha solver available")
        return None

    def _solve_ocr(self, image_bytes: bytes) -> Optional[str]:
        """Preprocess image and extract text with Tesseract OCR."""
        try:
            img = Image.open(io.BytesIO(image_bytes)).convert("L")
            w, h = img.size
            # Upscale for better OCR accuracy
            img = img.resize((w * 3, h * 3), resample=Image.Resampling.LANCZOS)
            # Enhance contrast
            img = ImageEnhance.Contrast(img).enhance(2.5)
            # Binarize
            img = img.point(lambda p: 255 if p > 130 else 0)
            # Sharpen
            img = img.filter(ImageFilter.SHARPEN)
            # Denoise
            img = img.filter(ImageFilter.MedianFilter(size=3))

            # OCR with multiple configs
            configs = [
                '--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789',
                '--oem 3 --psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789',
                '--oem 3 --psm 6',
            ]

            for config in configs:
                text = pytesseract.image_to_string(img, config=config).strip()
                # Clean up
                text = ''.join(c for c in text if c.isalnum())
                if len(text) >= 3:
                    logger.info(f"OCR solved CAPTCHA: {text}")
                    return text

            logger.warning("OCR failed to extract valid text from CAPTCHA")
            return None
        except Exception as e:
            logger.error(f"OCR error: {e}")
            return None

    def _solve_2captcha(self, image_bytes: bytes) -> Optional[str]:
        """Submit image to 2captcha service."""
        if not self._2captcha:
            return None
        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp.write(image_bytes)
                tmp_path = tmp.name
            result = self._2captcha.normal(tmp_path)
            os.unlink(tmp_path)
            return result.get("code") if isinstance(result, dict) else str(result)
        except Exception as e:
            logger.error(f"2captcha image solve failed: {e}")
            return None

    def _solve_anticaptcha(self, image_bytes: bytes) -> Optional[str]:
        """Submit image to Anti-Captcha service."""
        if not self._anticaptcha:
            return None
        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp.write(image_bytes)
                tmp_path = tmp.name
            result = self._anticaptcha.solve_and_return_solution(tmp_path)
            os.unlink(tmp_path)
            return result
        except Exception as e:
            logger.error(f"Anti-captcha image solve failed: {e}")
            return None

    def _solve_manual(self, image_bytes: bytes) -> Optional[str]:
        """Save image and prompt user for manual input."""
        try:
            captcha_path = "sessions/captcha_manual.png"
            os.makedirs("sessions", exist_ok=True)
            with open(captcha_path, "wb") as f:
                f.write(image_bytes)

            # Try to open image with default viewer
            import platform
            import subprocess
            sys_name = platform.system()
            try:
                if sys_name == "Windows":
                    os.startfile(captcha_path)
                elif sys_name == "Darwin":
                    subprocess.run(["open", captcha_path])
                else:
                    subprocess.run(["xdg-open", captcha_path])
            except:
                pass

            text = input("\n[MANUAL CAPTCHA] Enter the text from the image: ").strip()
            return text if text else None
        except Exception as e:
            logger.error(f"Manual CAPTCHA error: {e}")
            return None
