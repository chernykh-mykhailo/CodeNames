from PIL import Image, ImageDraw, ImageFont
import io
import logging
from typing import List, Dict
from src.games.codenames.engine import CardColor

logger = logging.getLogger(__name__)

class CodenamesRenderer:
    def __init__(self, font_path: str | None = None):
        if font_path is None:
            import platform
            if platform.system() == "Windows":
                self.font_path = "C:/Windows/Fonts/arial.ttf"
            else:
                self.font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        else:
            self.font_path = font_path

        self.card_size = (200, 100)
        self.padding = 10

        # ── Preload all font sizes once at init ──
        self._font_cache: dict[int, ImageFont.FreeTypeFont] = {}
        for size in range(12, 27):
            try:
                self._font_cache[size] = ImageFont.truetype(self.font_path, size)
            except Exception:
                default = ImageFont.load_default()
                for s in range(12, 27):
                    self._font_cache[s] = default
                break

        # ── Background image cache ──
        self._bg_cache: dict[tuple, Image.Image] = {}

        # Default colours (no custom overrides)
        self.colors = {
            CardColor.GREEN: (60, 180, 60),
            CardColor.RED: (220, 60, 60),
            CardColor.BYSTANDER: (240, 220, 180),
            CardColor.ASSASSIN: (0, 0, 0),
            "hidden": (210, 210, 210),
            "text_dark": (20, 20, 20),
        }
        self.dark_colors = {
            CardColor.GREEN: (80, 180, 80),
            CardColor.RED: (220, 60, 60),
            CardColor.BYSTANDER: (160, 150, 120),
            CardColor.ASSASSIN: (0, 0, 0),
            "hidden": (35, 38, 48),
            "bg": (15, 15, 18),
            "text": (255, 255, 255),
            "outline": (70, 70, 80),
        }
        self.custom_light: Dict = {}
        self.custom_dark: Dict = {}

    # ─────────────────────────────────────────
    #  Public helpers
    # ─────────────────────────────────────────

    def set_custom_colors(self, light_colors: Dict, dark_colors: Dict):
        self.custom_light = light_colors or {}
        self.custom_dark = dark_colors or {}

    def clear_cache(self):
        self._bg_cache.clear()

    @staticmethod
    def hex_to_rgb(hex_str: str | None, default: tuple) -> tuple:
        if not hex_str:
            return default
        try:
            h = hex_str.lstrip("#")
            return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))
        except Exception:
            return default

    @staticmethod
    def _apply_opacity(color: tuple, opacity: float) -> tuple:
        alpha = max(0, min(255, int(opacity * 255)))
        return (*color, alpha)

    def _get_single_line_word(self, word: str) -> str:
        return word.strip().upper()

    # ─────────────────────────────────────────
    #  Font sizing (uses cache, no disk reads)
    # ─────────────────────────────────────────

    def _get_font_for_word(self, word: str, max_width: int, max_height: int):
        for size in range(26, 12, -1):
            font = self._font_cache.get(size)
            if font is None:
                font = ImageFont.load_default()
            bbox = font.getbbox(word)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            if w <= max_width - 15 and h <= max_height - 10:
                return font, h
        return self._font_cache.get(14, ImageFont.load_default()), 14

    # ─────────────────────────────────────────
    #  Background rendering (cached)
    # ─────────────────────────────────────────

    def _get_bg_image(self, path: str, width: int, height: int, opacity: float) -> Image.Image | None:
        key = (path, width, height, opacity)
        cached = self._bg_cache.get(key)
        if cached is not None:
            return cached

        try:
            with open(path, "rb") as f:
                img = Image.open(io.BytesIO(f.read()))
            # Handle animated GIF → first frame
            if getattr(img, "is_animated", False):
                img.seek(0)
            img = img.convert("RGBA")
            img = img.resize((width, height), Image.LANCZOS)
            if opacity < 1.0:
                alpha = img.split()[3].point(lambda p: int(p * opacity))
                img.putalpha(alpha)
            self._bg_cache[key] = img
            return img
        except Exception as e:
            logger.error(f"Background load failed: {path}: {e}")
            return None

    # ─────────────────────────────────────────
    #  Main board renderer
    # ─────────────────────────────────────────

    def render_board(
        self,
        cards: List[Dict],
        spymaster_view: bool = False,
        dark_mode: bool = False,
        background_image: str | None = None,
        background_opacity: float = 1.0,
        card_background_opacity: float = 1.0,
    ) -> io.BytesIO:
        import math

        total_cards = len(cards)
        grid_size = int(math.sqrt(total_cards))
        cw, ch = self.card_size
        pad = self.padding
        width = grid_size * (cw + pad) + pad
        height = grid_size * (ch + pad) + pad

        # ── Colour palette ──
        if dark_mode:
            bg_color = self.hex_to_rgb(self.custom_dark.get("bg"), self.dark_colors["bg"])
            hidden_color = self.hex_to_rgb(self.custom_dark.get("hidden"), self.dark_colors["hidden"])
            text_color_main = self.hex_to_rgb(self.custom_dark.get("text"), self.dark_colors["text"])
            outline_color = self.hex_to_rgb(self.custom_dark.get("outline"), self.dark_colors["outline"])
            theme = {
                CardColor.GREEN: self.hex_to_rgb(self.custom_dark.get(CardColor.GREEN.value), self.dark_colors[CardColor.GREEN]),
                CardColor.RED: self.hex_to_rgb(self.custom_dark.get(CardColor.RED.value), self.dark_colors[CardColor.RED]),
                CardColor.BYSTANDER: self.hex_to_rgb(self.custom_dark.get(CardColor.BYSTANDER.value), self.dark_colors[CardColor.BYSTANDER]),
                CardColor.ASSASSIN: self.hex_to_rgb(self.custom_dark.get(CardColor.ASSASSIN.value), self.dark_colors[CardColor.ASSASSIN]),
            }
        else:
            bg_color = self.hex_to_rgb(self.custom_light.get("bg"), (235, 235, 235))
            hidden_color = self.hex_to_rgb(self.custom_light.get("hidden"), self.colors["hidden"])
            text_color_main = self.hex_to_rgb(self.custom_light.get("text_dark"), self.colors["text_dark"])
            outline_color = self.hex_to_rgb(self.custom_light.get("outline"), (180, 180, 180))
            theme = {
                CardColor.GREEN: self.hex_to_rgb(self.custom_light.get(CardColor.GREEN.value), self.colors[CardColor.GREEN]),
                CardColor.RED: self.hex_to_rgb(self.custom_light.get(CardColor.RED.value), self.colors[CardColor.RED]),
                CardColor.BYSTANDER: self.hex_to_rgb(self.custom_light.get(CardColor.BYSTANDER.value), self.colors[CardColor.BYSTANDER]),
                CardColor.ASSASSIN: self.hex_to_rgb(self.custom_light.get(CardColor.ASSASSIN.value), self.colors[CardColor.ASSASSIN]),
            }

        # ── Create base image (RGBA for alpha compositing) ──
        base = Image.new("RGBA", (width, height), (*bg_color, 255))

        # ── Paste background image (cached) ──
        if background_image:
            bg_img = self._get_bg_image(background_image, width, height, background_opacity)
            if bg_img is not None:
                base.paste(bg_img, (0, 0), bg_img)

        # ── Flat RGB for final drawing ──
        flat = Image.new("RGB", (width, height), bg_color)
        flat.paste(base, (0, 0))

        # ── Resolve each card ──
        if not hasattr(self, "_card_cache"):
            self._card_cache = {}

        for i, card in enumerate(cards):
            x = (i % grid_size) * (cw + pad) + pad
            y = (i // grid_size) * (ch + pad) + pad

            # Determine cache key for the card layout
            is_revealed_flag = False
            if isinstance(card, dict):
                word = self._get_single_line_word(card["word"])
                color_val = card["color"].value if hasattr(card["color"], "value") else card["color"]
                is_revealed_flag = card.get("is_revealed", False)
                color_a_val = card.get("color_a").value if card.get("color_a") and hasattr(card.get("color_a"), "value") else (card.get("color_a") if card.get("color_a") else None)
                color_b_val = card.get("color_b").value if card.get("color_b") and hasattr(card.get("color_b"), "value") else (card.get("color_b") if card.get("color_b") else None)
                revealed_color_val = card.get("revealed_color").value if card.get("revealed_color") and hasattr(card.get("revealed_color"), "value") else (card.get("revealed_color") if card.get("revealed_color") else None)
            else:
                word = self._get_single_line_word(card.word)
                color_val = card.color.value if hasattr(card.color, "value") else card.color
                is_revealed_flag = card.is_revealed if hasattr(card, "is_revealed") else False
                color_a_val = card.color_a.value if hasattr(card, "color_a") and card.color_a and hasattr(card.color_a, "value") else (card.color_a if hasattr(card, "color_a") else None)
                color_b_val = card.color_b.value if hasattr(card, "color_b") and card.color_b and hasattr(card.color_b, "value") else (card.color_b if hasattr(card, "color_b") else None)
                revealed_color_val = card.revealed_color.value if hasattr(card, "revealed_color") and card.revealed_color and hasattr(card.revealed_color, "value") else (card.revealed_color if hasattr(card, "revealed_color") else None)

            # Card cache key components:
            # (word, color_val, is_revealed_flag, spymaster_view, color_a_val, color_b_val, revealed_color_val, dark_mode, background_image)
            card_key = (
                word,
                color_val,
                is_revealed_flag,
                spymaster_view,
                color_a_val,
                color_b_val,
                revealed_color_val,
                dark_mode,
                background_image
            )

            if card_key in self._card_cache:
                card_blended = self._card_cache[card_key]
                flat.paste(card_blended, (x, y))
                continue

            # ---- Determine colour(s) ----
            is_split = False
            is_revealed_split = False
            c_a = c_b = c_maj = c_min = None

            if isinstance(card, dict):
                if card.get("color_a") and card.get("color_b") and (spymaster_view or card.get("is_revealed")):
                    is_split = True
                    if card.get("is_revealed") and card.get("revealed_color"):
                        is_revealed_split = True
                        guessed = card["revealed_color"]
                        c_maj = theme[CardColor(guessed)]
                        c_min = theme[CardColor(card["color_b"] if guessed == card["color_a"] else card["color_a"])]
                    else:
                        c_a = theme[CardColor(card["color_a"])]
                        c_b = theme[CardColor(card["color_b"])]
                    color = theme[CardColor(card["color"])]
                else:
                    color = theme[CardColor(card["color"])] if (spymaster_view or card.get("is_revealed")) else hidden_color
            else:
                if hasattr(card, "color_a") and hasattr(card, "color_b") and (spymaster_view or card.is_revealed):
                    is_split = True
                    if card.is_revealed and hasattr(card, "revealed_color"):
                        is_revealed_split = True
                        guessed = card.revealed_color
                        c_maj = theme[CardColor(guessed)]
                        c_min = theme[CardColor(card.color_b if guessed == card.color_a else card.color_a)]
                    else:
                        c_a = theme[CardColor(card.color_a)]
                        c_b = theme[CardColor(card.color_b)]
                    color = theme[CardColor(card.color)]
                else:
                    color = theme[CardColor(card.color)] if (spymaster_view or card.is_revealed) else hidden_color

            # Crop background region to create the blended card
            bg_region = base.crop((x, y, x + cw, y + ch)).copy()
            card_img = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            cd = ImageDraw.Draw(card_img)

            # ---- Draw card body ----
            if is_split:
                if is_revealed_split:
                    cd.rounded_rectangle([0, 0, cw, ch], radius=10, fill=self._apply_opacity(c_maj, card_background_opacity))
                    cd.polygon([(cw, int(ch * 0.3)), (cw, ch), (int(cw * 0.3), ch)], fill=self._apply_opacity(c_min, card_background_opacity))
                else:
                    cd.rounded_rectangle([0, 0, cw, ch], radius=10, fill=self._apply_opacity(c_a, card_background_opacity))
                    cd.polygon([(cw, 0), (cw, ch), (0, ch)], fill=self._apply_opacity(c_b, card_background_opacity))
                
                blended = Image.alpha_composite(bg_region, card_img)
                # Apply board border outline directly on blended region
                cd_blend = ImageDraw.Draw(blended)
                cd_blend.rounded_rectangle([0, 0, cw, ch], radius=10, fill=None, outline=outline_color, width=2)
            else:
                cd.rounded_rectangle([0, 0, cw, ch], radius=10, fill=self._apply_opacity(color, card_background_opacity), outline=outline_color, width=2)
                blended = Image.alpha_composite(bg_region, card_img)

            # ---- Text colour ----
            if dark_mode:
                t_color = text_color_main
            elif is_split:
                r1, g1, b1 = c_maj if is_revealed_split else c_a
                r2, g2, b2 = c_min if is_revealed_split else c_b
                avg = ((r1 * 299 + g1 * 587 + b1 * 114) + (r2 * 299 + g2 * 587 + b2 * 114)) / 2000
                t_color = self.hex_to_rgb(self.custom_light.get("text_light"), (255, 255, 255)) if avg < 150 else text_color_main
            else:
                r, g, b = color
                brightness = (r * 299 + g * 587 + b * 114) / 1000
                t_color = self.hex_to_rgb(self.custom_light.get("text_light"), (255, 255, 255)) if brightness < 150 else text_color_main

            # ---- Draw word ----
            font, _ = self._get_font_for_word(word, cw, ch)
            cx = cw // 2
            cy = ch // 2
            blended_draw = ImageDraw.Draw(blended)
            blended_draw.text((cx, cy), word, fill=t_color, font=font, anchor="mm")

            # ---- Spymaster cross-out ----
            if is_revealed_flag and spymaster_view:
                p = 10
                blended_draw.line([p, p, cw - p, ch - p], fill=t_color, width=4)
                blended_draw.line([p, ch - p, cw - p, p], fill=t_color, width=4)

            # Store the final blended card sub-image in cache
            card_blended_rgb = Image.new("RGB", (cw, ch), bg_color)
            card_blended_rgb.paste(blended, (0, 0))
            self._card_cache[card_key] = card_blended_rgb

            flat.paste(card_blended_rgb, (x, y))

        # ── Encode to WEBP (faster and smaller than PNG) ──
        buf = io.BytesIO()
        flat.save(buf, format="WEBP", quality=90)
        buf.seek(0)
        return buf


BoardRenderer = CodenamesRenderer