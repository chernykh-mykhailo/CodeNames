import random
import itertools
from typing import List, Dict, Tuple, Optional
from .engine import CodenamesEngine, Team, CardColor


class AIBot:
    """
    AI Spymaster that generates clues automatically.
    Uses semantic association heuristics to find good clues.
    """
    
    # Semantic associations - word pairs that are commonly related
    SEMANTIC_ASSOCIATIONS = {
        # Ukrainian
        "вода": ["річка", "море", "океан", "дощ", "пляж", "плавати", "риба", "лодка", "хвиля"],
        "вогонь": ["полум'я", "піч", "світло", "тепло", "сірник", "вугілля", "дим", "горіти"],
        "земля": ["грунт", "поле", "сад", "трава", "дерево", "гора", "пісок", "камінь"],
        "небо": ["хмара", "сонце", "місяць", "зірка", "птах", "літак", "блакитний", "високо"],
        "час": ["годинник", "хвилина", "секунда", "день", "рік", "минуле", "майбутнє", "вечір"],
        "дім": ["хата", "квартира", "кімната", "вікно", "двері", "дах", "стіна", "сім'я"],
        "школа": ["учень", "вчитель", "клас", "урок", "книга", "зошит", "ручка", "екзамен"],
        "робота": ["офіс", "начальник", "зарплата", "колега", "проект", "документ", "комп'ютер"],
        "їжа": ["хліб", "м'ясо", "риба", "овочі", "фрукти", "суп", "салат", "солодке"],
        "транспорт": ["авто", "машина", "автобус", "трамвай", "метро", "потяг", "літак", "корабель"],
        "спорт": ["футбол", "баскетбол", "теніс", "біг", "плавання", "м'яч", "гімнастика", "змагання"],
        "музика": ["пісня", "мелодія", "ритм", "нот", "співати", "інструмент", "концерт", "оркестр"],
        "кіно": ["фільм", "актор", "режисер", "екран", "квиток", "сеанс", "спектакль", "театр"],
        "книга": ["роман", "повість", "автор", "герой", "сюжет", "сторінка", "бібліотека", "читати"],
        "місто": ["вулиця", "площа", "будинок", "парк", "магазин", "кафе", "автобус", "метро"],
        # English
        "water": ["river", "sea", "ocean", "rain", "beach", "swim", "fish", "boat", "wave"],
        "fire": ["flame", "stove", "light", "heat", "match", "coal", "smoke", "burn"],
        "earth": ["soil", "field", "garden", "grass", "tree", "mountain", "sand", "stone"],
        "sky": ["cloud", "sun", "moon", "star", "bird", "plane", "blue", "high"],
        "time": ["clock", "minute", "second", "day", "year", "past", "future", "evening"],
        "home": ["house", "apartment", "room", "window", "door", "roof", "wall", "family"],
        "school": ["student", "teacher", "class", "lesson", "book", "notebook", "pen", "exam"],
        "work": ["office", "boss", "salary", "colleague", "project", "document", "computer"],
        "food": ["bread", "meat", "fish", "vegetables", "fruits", "soup", "salad", "sweet"],
        "transport": ["car", "bus", "tram", "metro", "train", "plane", "ship"],
        "sports": ["football", "basketball", "tennis", "running", "swimming", "ball", "gymnastics"],
        "music": ["song", "melody", "rhythm", "note", "sing", "instrument", "concert", "orchestra"],
        "movie": ["film", "actor", "director", "screen", "ticket", "show", "theater"],
        "book": ["novel", "story", "author", "hero", "plot", "page", "library", "read"],
        "city": ["street", "square", "building", "park", "shop", "cafe", "bus", "metro"],
    }
    
    # Word stems/prefixes for finding common roots
    WORD_STEMS = {
        "вод": ["вода", "водний", "підводний", "наводнення"],
        "вогн": ["вогонь", "вогняний", "запалити", "пожежа"],
        "земл": ["земля", "земний", "поземний", "наземний"],
        "неб": ["небо", "небесний", "піднебесний"],
        "час": ["час", "часовий", "часовик"],
        "дом": ["дім", "домашній", "будинок"],
        "школ": ["школа", "шкільний", "учениця"],
        "роб": ["робота", "робочий", "працювати"],
        "їж": ["їжа", "їсти", "харчування"],
        "трансп": ["транспорт", "перевезення"],
        "спорт": ["спорт", "спортивний"],
        "музик": ["музика", "музичний"],
        "кін": ["кіно", "кінематограф"],
        "книг": ["книга", "книжковий"],
        "міст": ["місто", "міський"],
    }
    
    DIFFICULTY_LEVELS = {
        "easy": {
            "max_clues": 2,
            "min_association_strength": 0.7,
            "use_hints": True,
            "hint_frequency": 0.8
        },
        "medium": {
            "max_clues": 3,
            "min_association_strength": 0.5,
            "use_hints": True,
            "hint_frequency": 0.5
        },
        "hard": {
            "max_clues": 3,
            "min_association_strength": 0.3,
            "use_hints": False,
            "hint_frequency": 0.2
        }
    }
    
    def __init__(self, language: str = "uk", difficulty: str = "medium"):
        self.language = language
        self.difficulty = difficulty
        self.config = self.DIFFICULTY_LEVELS.get(difficulty, self.DIFFICULTY_LEVELS["medium"])
    
    def generate_clue(self, engine: CodenamesEngine, team: Team) -> Optional[Tuple[str, int, str]]:
        """
        Generate a clue for the given team.
        Returns: (clue_word, count, explanation) or None if no good clue found
        """
        # Get unrevealed cards for the team
        team_color = CardColor.GREEN if team == Team.GREEN else CardColor.RED
        team_words = []
        other_team_words = []
        assassin_words = []
        bystander_words = []
        
        for i, card in enumerate(engine.board):
            if card.is_revealed:
                continue
            
            if card.color == team_color:
                team_words.append((i, card.word))
            elif card.color == CardColor.ASSASSIN:
                assassin_words.append((i, card.word))
            elif card.color in [CardColor.GREEN, CardColor.RED]:
                other_team_words.append((i, card.word))
            else:
                bystander_words.append((i, card.word))
        
        if not team_words:
            return None
        
        # Try to find good clues for 1-3 words
        best_clues = []
        
        for num_words in range(1, min(self.config["max_clues"], len(team_words)) + 1):
            for word_combo in itertools.combinations(team_words, num_words):
                clue = self._find_clue_for_words(
                    [w for _, w in word_combo],
                    [w for _, w in other_team_words],
                    [w for _, w in assassin_words],
                    [w for _, w in bystander_words]
                )
                if clue:
                    score = self._score_clue(clue, num_words)
                    best_clues.append((clue, word_combo, score))
        
        if not best_clues:
            return None
        
        # Sort by score and pick the best
        best_clues.sort(key=lambda x: x[2], reverse=True)
        best_clue, word_combo, _ = best_clues[0]
        
        explanation = self._generate_explanation(best_clue, [w for _, w in word_combo])
        return (best_clue, len(word_combo), explanation)
    
    def _find_clue_for_words(self, target_words: List[str], 
                            other_words: List[str],
                            assassin_words: List[str],
                            bystander_words: List[str]) -> Optional[str]:
        """Find a clue that connects target words but avoids others."""
        
        # Find common associations
        common_associations = {}
        
        for word in target_words:
            word_lower = word.lower()
            associations = self.SEMANTIC_ASSOCIATIONS.get(word_lower, [])
            
            for assoc in associations:
                if assoc not in common_associations:
                    common_associations[assoc] = 0
                common_associations[assoc] += 1
        
        # Filter associations that connect to target words
        good_clues = []
        for clue, count in common_associations.items():
            if count >= len(target_words) * self.config["min_association_strength"]:
                # Check if clue conflicts with other words
                if not self._conflicts_with_words(clue, other_words + assassin_words + bystander_words):
                    good_clues.append(clue)
        
        if not good_clues:
            # Try word stems
            for stem, related_words in self.WORD_STEMS.items():
                matches = sum(1 for word in target_words if stem in word.lower())
                if matches >= len(target_words) * self.config["min_association_strength"]:
                    clue = random.choice(related_words)
                    if not self._conflicts_with_words(clue, other_words + assassin_words + bystander_words):
                        good_clues.append(clue)
        
        if not good_clues:
            # Fallback: use broader semantic categories
            category_clues = self._find_category_clues(target_words, other_words + assassin_words + bystander_words)
            if category_clues:
                good_clues.extend(category_clues)

        if not good_clues:
            # Last resort: use a very general word that's unlikely to conflict
            general_clues = ["концепт", "категорія", "група", "тип", "клас"]
            if self.language == "en":
                general_clues = ["concept", "category", "group", "type", "class"]

            for clue in general_clues:
                if not self._conflicts_with_words(clue, other_words + assassin_words):
                    good_clues.append(clue)
                    break

        if good_clues:
            return random.choice(good_clues)

        return None
    
    def _conflicts_with_words(self, clue: str, words: List[str]) -> bool:
        """Check if clue strongly conflicts with given words."""
        clue_lower = clue.lower()
        
        for word in words:
            word_lower = word.lower()
            # Direct word match
            if clue_lower == word_lower or clue_lower in word_lower or word_lower in clue_lower:
                return True
            
            # Check associations
            associations = self.SEMANTIC_ASSOCIATIONS.get(word_lower, [])
            if clue_lower in associations:
                return True
        
        return False
    
    def _score_clue(self, clue: str, num_words: int) -> float:
        """Score a clue based on quality."""
        # Higher score for more words
        score = num_words * 10
        
        # Bonus for longer, more specific clues
        if len(clue) > 4:
            score += 5
        
        return score
    
    def _generate_explanation(self, clue: str, target_words: List[str]) -> str:
        """Generate explanation based on difficulty."""

        if self.difficulty == "easy":
            # Very obvious hints
            if self.language == "uk":
                return f"💡 Підказка: '{clue}' пов'язане зі словами: {', '.join(target_words)}"
            else:
                return f"💡 Hint: '{clue}' is related to: {', '.join(target_words)}"

        elif self.difficulty == "medium":
            # Moderate hints - show connection type
            connections = []
            for word in target_words:
                if clue.lower() in word.lower() or word.lower() in clue.lower():
                    connections.append(f"{word} (частина слова)")
                else:
                    connections.append(word)

            if self.language == "uk":
                return f"🎯 Асоціація: '{clue}' -> {', '.join(connections)}"
            else:
                return f"🎯 Association: '{clue}' -> {', '.join(connections)}"

        else:  # hard
            # Cryptic hints
            if self.language == "uk":
                return f"🔮 Загадка: Шукаєте зв'язок через '{clue}'..."
            else:
                return f"🔮 Riddle: Seek connection through '{clue}'..."

    def _find_category_clues(self, target_words: List[str], forbidden_words: List[str]) -> List[str]:
        """Find broader category clues when specific associations fail."""
        categories = {
            "uk": {
                "тварини": ["собака", "кіт", "птах", "риба", "змія", "миша", "ведмідь", "лисиця"],
                "рослини": ["дерево", "квітка", "трава", "кущ", "мох", "папороть", "кактус"],
                "предмети": ["стіл", "стілець", "ліжко", "шафа", "двері", "вікно", "лампа"],
                "їжа": ["хліб", "м'ясо", "риба", "суп", "салат", "каша", "пиріг", "торт"],
                "транспорт": ["авто", "літак", "потяг", "корабель", "велосипед", "мотоцикл"],
                "спортивні": ["м'яч", "ракетка", "ключка", "штанга", "медаль", "кубок"],
                "музичні": ["гітара", "піаніно", "скрипка", "барабан", "мікрофон", "ноти"],
            },
            "en": {
                "animals": ["dog", "cat", "bird", "fish", "snake", "mouse", "bear", "fox"],
                "plants": ["tree", "flower", "grass", "bush", "moss", "fern", "cactus"],
                "objects": ["table", "chair", "bed", "wardrobe", "door", "window", "lamp"],
                "food": ["bread", "meat", "fish", "soup", "salad", "porridge", "pie", "cake"],
                "transport": ["car", "plane", "train", "ship", "bicycle", "motorcycle"],
                "sports": ["ball", "racket", "stick", "barbell", "medal", "cup"],
                "musical": ["guitar", "piano", "violin", "drum", "microphone", "notes"],
            }
        }

        lang_categories = categories.get(self.language, {})
        good_clues = []

        for category, words_in_category in lang_categories.items():
            # Check if multiple target words belong to this category
            matches = sum(1 for word in target_words if word.lower() in words_in_category)
            if matches >= 2:  # At least 2 words in this category
                if not self._conflicts_with_words(category, forbidden_words):
                    good_clues.append(category)

        return good_clues
