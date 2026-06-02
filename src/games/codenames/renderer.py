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
        
        # Colors (Rich Palette)
        self.colors = {
            CardColor.GREEN: (60, 180, 60),    # Vibrant Green
            CardColor.RED: (220, 60, 60),      # Solid Red
            CardColor.BYSTANDER: (240, 220, 180), # Light Beige
            CardColor.ASSASSIN: (0, 0, 0),     # ABSOLUTE PITCH BLACK
            "hidden": (210, 210, 210),         # Light Grey
            "text_dark": (20, 20, 20)
        }
        
        # Dark mode base colors
        self.dark_colors = {
            CardColor.GREEN: (80, 180, 80),
            CardColor.RED: (220, 60, 60),
            CardColor.BYSTANDER: (160, 150, 120),
            CardColor.ASSASSIN: (0, 0, 0),
            "hidden": (35, 38, 48),
            "bg": (15, 15, 18),
            "text": (255, 255, 255),
            "outline": (70, 70, 80)
        }
        
        self.custom_light = {}
        self.custom_dark = {}

    def set_custom_colors(self, light_colors: Dict, dark_colors: Dict):
        self.custom_light = light_colors or {}
        self.custom_dark = dark_colors or {}
        
    @staticmethod
    def hex_to_rgb(hex_str: str | None, default: tuple) -> tuple:
        if not hex_str:
            return default
        try:
            h = hex_str.lstrip('#')
            return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        except Exception:
            return default
        
    def _get_single_line_word(self, word: str) -> str:
        return word.strip().upper()

    def _get_font_for_word(self, word: str, max_width: int, max_height: int):
        # Professional elegant sizing for a single line
        # Start with a larger size and shrink until it fits
        for size in range(26, 12, -1):
            try:
                font = ImageFont.truetype(self.font_path, size)
            except Exception as e:
                logger.error(f"Failed to load font: {e}")
                return ImageFont.load_default(), size
            
            bbox = font.getbbox(word)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            
            if w <= max_width - 15 and h <= max_height - 10:
                return font, h
        return ImageFont.load_default(), 14

    def render_board(self, cards: List[Dict], spymaster_view: bool = False, dark_mode: bool = False) -> io.BytesIO:
        import math
        total_cards = len(cards)
        grid_size = int(math.sqrt(total_cards))
        
        width = grid_size * (self.card_size[0] + self.padding) + self.padding
        height = grid_size * (self.card_size[1] + self.padding) + self.padding
        
        # Merge defaults with custom overrides
        if dark_mode:
            bg_color = self.hex_to_rgb(self.custom_dark.get("bg"), self.dark_colors["bg"])
            hidden_color = self.hex_to_rgb(self.custom_dark.get("hidden"), self.dark_colors["hidden"])
            text_color_main = self.hex_to_rgb(self.custom_dark.get("text"), self.dark_colors["text"])
            outline_color = self.hex_to_rgb(self.custom_dark.get("outline"), self.dark_colors["outline"])
            
            theme_colors = {
                CardColor.GREEN: self.hex_to_rgb(self.custom_dark.get(CardColor.GREEN.value), self.dark_colors[CardColor.GREEN]),
                CardColor.RED: self.hex_to_rgb(self.custom_dark.get(CardColor.RED.value), self.dark_colors[CardColor.RED]),
                CardColor.BYSTANDER: self.hex_to_rgb(self.custom_dark.get(CardColor.BYSTANDER.value), self.dark_colors[CardColor.BYSTANDER]),
                CardColor.ASSASSIN: self.hex_to_rgb(self.custom_dark.get(CardColor.ASSASSIN.value), self.dark_colors[CardColor.ASSASSIN])
            }
        else:
            bg_color = self.hex_to_rgb(self.custom_light.get("bg"), (235, 235, 235))
            hidden_color = self.hex_to_rgb(self.custom_light.get("hidden"), self.colors["hidden"])
            text_color_main = self.hex_to_rgb(self.custom_light.get("text_dark"), self.colors["text_dark"])
            outline_color = self.hex_to_rgb(self.custom_light.get("outline"), (180, 180, 180))
            
            theme_colors = {
                CardColor.GREEN: self.hex_to_rgb(self.custom_light.get(CardColor.GREEN.value), self.colors[CardColor.GREEN]),
                CardColor.RED: self.hex_to_rgb(self.custom_light.get(CardColor.RED.value), self.colors[CardColor.RED]),
                CardColor.BYSTANDER: self.hex_to_rgb(self.custom_light.get(CardColor.BYSTANDER.value), self.colors[CardColor.BYSTANDER]),
                CardColor.ASSASSIN: self.hex_to_rgb(self.custom_light.get(CardColor.ASSASSIN.value), self.colors[CardColor.ASSASSIN])
            }

        image = Image.new("RGB", (width, height), bg_color)
        draw = ImageDraw.Draw(image)

        for i, card in enumerate(cards):
            x = (i % grid_size) * (self.card_size[0] + self.padding) + self.padding
            y = (i // grid_size) * (self.card_size[1] + self.padding) + self.padding
            
            # Determine card color
            if spymaster_view or card["is_revealed"]:
                color = theme_colors[CardColor(card["color"])]
            else:
                color = hidden_color
            
            # Draw card background
            draw.rounded_rectangle(
                [x, y, x + self.card_size[0], y + self.card_size[1]], 
                radius=10, 
                fill=color, 
                outline=outline_color,
                width=2
            )
            
            # Text color logic
            if dark_mode:
                t_color = text_color_main
            else:
                # Use brightness to decide text color (YIQ formula)
                r, g, b = color
                brightness = (r * 299 + g * 587 + b * 114) / 1000
                if brightness < 150:
                    t_color = self.hex_to_rgb(self.custom_light.get("text_light"), (255, 255, 255))
                else:
                    t_color = text_color_main
                
            # Draw word
            word = self._get_single_line_word(card["word"])
            font, text_h = self._get_font_for_word(word, self.card_size[0], self.card_size[1])
            
            # Custom drawing for letter spacing
            letter_spacing = 1
            
            # Calculate total width with spacing
            line_w = 0
            for char in word:
                c_bbox = draw.textbbox((0, 0), char, font=font)
                line_w += (c_bbox[2] - c_bbox[0]) + letter_spacing
            line_w -= letter_spacing # Remove last spacing
            
            text_x = x + (self.card_size[0] - line_w) / 2
            text_y = y + (self.card_size[1] - text_h) / 2 - 2
            
            # Draw character by character
            temp_x = text_x
            for char in word:
                draw.text((temp_x, text_y), char, fill=t_color, font=font)
                c_bbox = draw.textbbox((0, 0), char, font=font)
                temp_x += (c_bbox[2] - c_bbox[0]) + letter_spacing
            
            # Cross out if revealed (only for spymaster view, public view uses colors to indicate reveal)
            if card["is_revealed"] and spymaster_view:
                # Draw an X across the entire card
                padding = 10
                x1 = x + padding
                y1 = y + padding
                x2 = x + self.card_size[0] - padding
                y2 = y + self.card_size[1] - padding
                
                # Top-left to bottom-right
                draw.line([x1, y1, x2, y2], fill=t_color, width=4)
                # Bottom-left to top-right
                draw.line([x1, y2, x2, y1], fill=t_color, width=4)
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return img_byte_arr

BoardRenderer = CodenamesRenderer

