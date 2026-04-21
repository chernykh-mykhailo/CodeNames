from PIL import Image, ImageDraw, ImageFont
import io
import logging
from typing import List, Dict
from src.games.codenames.engine import CardColor

logger = logging.getLogger(__name__)

class BoardRenderer:
    def __init__(self, font_path: str = None):
        if font_path is None:
            import platform
            if platform.system() == "Windows":
                self.font_path = "C:/Windows/Fonts/arialbd.ttf"
            else:
                self.font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        else:
            self.font_path = font_path
            
        self.card_size = (200, 100)
        self.padding = 10
        self.grid_size = 5
        
        # Colors (Rich Palette)
        self.colors = {
            CardColor.RED: (220, 40, 40),      # Solid Red
            CardColor.BLUE: (40, 80, 220),     # Solid Blue
            CardColor.BYSTANDER: (240, 220, 180), # Light Beige
            CardColor.ASSASSIN: (0, 0, 0),     # ABSOLUTE PITCH BLACK
            "hidden": (210, 210, 210),         # Light Grey
            "text_light": (255, 255, 255),
            "text_dark": (20, 20, 20)
        }
        
    def _split_long_word(self, word: str) -> List[str]:
        # Split words that are long or have hyphens
        if "-" in word:
            return word.split("-")
            
        if len(word) <= 9:
            return [word]
        
        # Split into two lines at roughly half
        mid = len(word) // 2
        return [word[:mid], word[mid:]]

    def _get_font_for_lines(self, lines: List[str], max_width: int, max_height: int, dark_mode: bool = False):
        # Slightly larger font range for better readability
        for size in range(32, 14, -2):
            try:
                font = ImageFont.truetype(self.font_path, size)
            except Exception as e:
                logger.error(f"Failed to load font at {self.font_path} (size {size}): {e}")
                return ImageFont.load_default(), 20
            
            can_fit = True
            total_h = 0
            for line in lines:
                bbox = font.getbbox(line)
                w = bbox[2] - bbox[0]
                h = bbox[3] - bbox[1]
                if w > max_width - 15: # Tightened padding
                    can_fit = False
                    break
                total_h += h + 3
            
            if can_fit and total_h <= max_height - 10:
                return font, total_h
        return ImageFont.load_default(), 20

    def render_board(self, cards: List[Dict], spymaster_view: bool = False, dark_mode: bool = False) -> io.BytesIO:
        width = self.grid_size * (self.card_size[0] + self.padding) + self.padding
        height = self.grid_size * (self.card_size[1] + self.padding) + self.padding
        
        # Dark Mode Palette Overrides
        if dark_mode:
            bg_color = (15, 15, 18)
            hidden_color = (35, 38, 48)
            text_color_main = (255, 255, 255)
            outline_color = (70, 70, 80)
            
            # Distinct Dark Mode Palette
            theme_colors = {
                CardColor.RED: (210, 60, 60),
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
            x = (i % self.grid_size) * (self.card_size[0] + self.padding) + self.padding
            y = (i // self.grid_size) * (self.card_size[1] + self.padding) + self.padding
            
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
                if color in [self.colors[CardColor.RED], self.colors[CardColor.BLUE], self.colors[CardColor.ASSASSIN]]:
                    t_color = self.colors["text_light"]
                else:
                    t_color = text_color_main
                
            # Draw word
            word = card["word"].upper()
            lines = self._split_long_word(word)
            font, total_h = self._get_font_for_lines(lines, self.card_size[0], self.card_size[1], dark_mode)
            
            current_y = y + (self.card_size[1] - total_h) / 2
            for line in lines:
                # Custom drawing for letter spacing
                letter_spacing = 2
                
                # Calculate total width with spacing
                line_w = 0
                for char in line:
                    c_bbox = draw.textbbox((0, 0), char, font=font)
                    line_w += (c_bbox[2] - c_bbox[0]) + letter_spacing
                line_w -= letter_spacing # Remove last spacing
                
                text_x = x + (self.card_size[0] - line_w) / 2
                
                # Draw character by character
                temp_x = text_x
                for char in line:
                    draw.text((temp_x, current_y), char, fill=t_color, font=font)
                    c_bbox = draw.textbbox((0, 0), char, font=font)
                    temp_x += (c_bbox[2] - c_bbox[0]) + letter_spacing
                
                # Strikethrough if revealed
                if card["is_revealed"]:
                    # Draw a black line through the middle of the text
                    line_y = current_y + (total_h / len(lines)) / 2 + 2
                    draw.line([text_x, line_y, text_x + line_w, line_y], fill=(0, 0, 0), width=3)
                
                current_y += (total_h / len(lines)) + 3
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return img_byte_arr
