from PIL import Image, ImageDraw, ImageFont
import io
from typing import List, Dict
from src.games.codenames.engine import CardColor

class BoardRenderer:
    def __init__(self, font_path: str = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        self.card_size = (200, 100)
        self.padding = 10
        self.grid_size = 5
        self.font_path = font_path
        
        # Colors (Rich Palette)
        self.colors = {
            CardColor.RED: (255, 77, 77),
            CardColor.BLUE: (77, 121, 255),
            CardColor.BYSTANDER: (200, 200, 180),
            CardColor.ASSASSIN: (50, 50, 50),
            "hidden": (245, 230, 204),
            "text_dark": (20, 20, 20),
            "text_light": (255, 255, 255)
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
            except Exception:
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
        
        # Background color
        bg_color = (30, 30, 30) if dark_mode else (225, 225, 225)
        hidden_color = (60, 60, 60) if dark_mode else self.colors["hidden"]
        text_dark = (220, 220, 220) if dark_mode else (20, 20, 20)
        outline_color = (80, 80, 80) if dark_mode else (160, 160, 160)

        image = Image.new("RGB", (width, height), bg_color)
        draw = ImageDraw.Draw(image)

        for i, card in enumerate(cards):
            x = (i % self.grid_size) * (self.card_size[0] + self.padding) + self.padding
            y = (i // self.grid_size) * (self.card_size[1] + self.padding) + self.padding
            
            # Determine card color
            if spymaster_view or card["is_revealed"]:
                color = self.colors[CardColor(card["color"])]
                if dark_mode:
                    # Slightly desaturate or darken for dark mode if needed
                    # For now keep classic vibrant colors as they pop
                    pass
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
            
            # Text color
            if color in [self.colors[CardColor.RED], self.colors[CardColor.BLUE], self.colors[CardColor.ASSASSIN]]:
                t_color = self.colors["text_light"]
            else:
                t_color = text_dark
                
            # Draw word (with wrap support)
            word = card["word"].upper()
            lines = self._split_long_word(word)
            font, total_h = self._get_font_for_lines(lines, self.card_size[0], self.card_size[1], dark_mode)
            
            current_y = y + (self.card_size[1] - total_h) / 2
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                w = bbox[2] - bbox[0]
                h = bbox[3] - bbox[1]
                text_x = x + (self.card_size[0] - w) / 2
                draw.text((text_x, current_y), line, fill=t_color, font=font)
                current_y += h + 3
            
            # Overlay if revealed in spymaster view
            if spymaster_view and card["is_revealed"]:
                draw.line([x, y, x + self.card_size[0], y + self.card_size[1]], fill=(0, 0, 0), width=3)
                draw.line([x + self.card_size[0], y, x, y + self.card_size[1]], fill=(0, 0, 0), width=3)

        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return img_byte_arr
