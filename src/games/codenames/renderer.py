from PIL import Image, ImageDraw, ImageFont
import io
import logging
from typing import List, Dict
from src.games.codenames.engine import CardColor

logger = logging.getLogger(__name__)

class CodenamesRenderer:
    def __init__(self, font_path: str = None):
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
            CardColor.BLUE: (40, 80, 220),     # Solid Blue
            CardColor.BYSTANDER: (240, 220, 180), # Light Beige
            CardColor.ASSASSIN: (0, 0, 0),     # ABSOLUTE PITCH BLACK
            "hidden": (210, 210, 210),         # Light Grey
            "text_light": (255, 255, 255),
            "text_dark": (20, 20, 20)
        }
        
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
        
        # Dark Mode Palette Overrides
        if dark_mode:
            bg_color = (15, 15, 18)
            hidden_color = (35, 38, 48)
            text_color_main = (255, 255, 255)
            outline_color = (70, 70, 80)
            
            # Distinct Dark Mode Palette
            theme_colors = {
                CardColor.GREEN: (80, 180, 80),
                CardColor.BLUE: (60, 100, 230),
                CardColor.BYSTANDER: (160, 150, 120), # Light Khaki/Sand
                CardColor.ASSASSIN: (0, 0, 0) # Pitch black
            }
        else:
            bg_color = (235, 235, 235)
            hidden_color = self.colors["hidden"] # Light Grey
            text_color_main = (20, 20, 20)
            outline_color = (180, 180, 180)
            theme_colors = self.colors # Using the new corrected dict here

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
                t_color = (255, 255, 255) # Always white in dark mode for better visibility
            else:
                if color in [self.colors[CardColor.GREEN], self.colors[CardColor.BLUE], self.colors[CardColor.ASSASSIN]]:
                    t_color = self.colors["text_light"]
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
                # Draw an X across the word text area
                padding = 4
                x1 = text_x - padding
                y1 = text_y - padding
                x2 = text_x + line_w + padding
                y2 = text_y + text_h + padding
                
                # Top-left to bottom-right
                draw.line([x1, y1, x2, y2], fill=t_color, width=3)
                # Bottom-left to top-right
                draw.line([x1, y2, x2, y1], fill=t_color, width=3)
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return img_byte_arr

BoardRenderer = CodenamesRenderer

