from PIL import Image, ImageDraw, ImageFont
import io
from typing import List, Dict
from src.games.codenames.engine import CardColor

class BoardRenderer:
    def __init__(self, font_path: str = "arial.ttf"):
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
            "text_dark": (30, 30, 30),
            "text_light": (240, 240, 240)
        }

    def render_board(self, cards: List[Dict], spymaster_view: bool = False) -> io.BytesIO:
        width = self.grid_size * (self.card_size[0] + self.padding) + self.padding
        height = self.grid_size * (self.card_size[1] + self.padding) + self.padding
        
        image = Image.new("RGB", (width, height), (240, 240, 240))
        draw = ImageDraw.Draw(image)
        
        try:
            font = ImageFont.truetype(self.font_path, 24)
        except:
            font = ImageFont.load_default()

        for i, card in enumerate(cards):
            x = (i % self.grid_size) * (self.card_size[0] + self.padding) + self.padding
            y = (i // self.grid_size) * (self.card_size[1] + self.padding) + self.padding
            
            # Determine card color
            if spymaster_view:
                color = self.colors[CardColor(card["color"])]
            elif card["is_revealed"]:
                color = self.colors[CardColor(card["color"])]
            else:
                color = self.colors["hidden"]
            
            # Draw card background
            draw.rounded_rectangle(
                [x, y, x + self.card_size[0], y + self.card_size[1]], 
                radius=8, 
                fill=color, 
                outline=(180, 180, 180)
            )
            
            # Text color
            if color in [self.colors[CardColor.RED], self.colors[CardColor.BLUE], self.colors[CardColor.ASSASSIN]]:
                text_color = self.colors["text_light"]
            else:
                text_color = self.colors["text_dark"]
                
            # Draw word
            word = card["word"].upper()
            w, h = draw.textbbox((0, 0), word, font=font)[2:]
            text_x = x + (self.card_size[0] - w) / 2
            text_y = y + (self.card_size[1] - h) / 2
            draw.text((text_x, text_y), word, fill=text_color, font=font)
            
            # Overlay if revealed in spymaster view
            if spymaster_view and card["is_revealed"]:
                draw.line([x, y, x + self.card_size[0], y + self.card_size[1]], fill=(0, 0, 0), width=3)
                draw.line([x + self.card_size[0], y, x, y + self.card_size[1]], fill=(0, 0, 0), width=3)

        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return img_byte_arr
