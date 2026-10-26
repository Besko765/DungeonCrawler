
from dataclasses import dataclass, field

from models.item import Item, ItemType


@dataclass
class Character:
    name: str
    character_class: str

    max_hp: int
    max_mp: int
    attack: int
    defense: int
    speed: int

    hp: int = 0
    mp: int = 0
    level: int = 1
    experience: int = 0
    gold: int = 0

    inventory: list[Item] = field(default_factory=list)
    weapon: Item | None = None
    armor: Item | None = None

    def __post_init__(self):
        if self.hp == 0:
            self.hp = self.max_hp
        if self.mp == 0:
            self.mp = self.max_mp

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    @property
    def total_attack(self) -> int:
        bonus = self.weapon.value if self.weapon else 0
        return self.attack + bonus

    @property
    def total_defense(self) -> int:
        bonus = self.armor.value if self.armor else 0
        return self.defense + bonus

    def take_damage(self, damage: int) -> int:
        actual_damage = max(1, damage - self.total_defense)
        self.hp = max(0, self.hp - actual_damage)
        return actual_damage

    def heal(self, amount: int) -> int:
        old_hp = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - old_hp

    def restore_mp(self, amount: int) -> int:
        old_mp = self.mp
        self.mp = min(self.max_mp, self.mp + amount)
        return self.mp - old_mp

    def add_item(self, item: Item) -> None:
        self.inventory.append(item)

    def use_item(self, index: int) -> str:
        if index < 0 or index >= len(self.inventory):
            return "Nie ma takiego przedmiotu."

        item = self.inventory[index]

        if item.item_type != ItemType.CONSUMABLE:
            return "Tego przedmiotu nie można teraz użyć."

        if item.name == "Mikstura zdrowia":
            restored = self.heal(item.value)
            if restored == 0:
                return "Masz już pełne zdrowie."
        elif item.name == "Mikstura many":
            restored = self.restore_mp(item.value)
            if restored == 0:
                return "Masz już pełną manę."
        else:
            return "Nie wiadomo, jak użyć tego przedmiotu."

        self.inventory.pop(index)
        return f"Użyto: {item.name}."

    def equip_item(self, index: int) -> str:
        if index < 0 or index >= len(self.inventory):
            return "Nie ma takiego przedmiotu."

        item = self.inventory[index]

        if item.item_type == ItemType.WEAPON:
            self.weapon = item
        elif item.item_type == ItemType.ARMOR:
            self.armor = item
        else:
            return "Tego przedmiotu nie można założyć."

        self.inventory.pop(index)
        return f"Założono: {item.name}."

    def gain_experience(self, amount: int) -> bool:
        self.experience += amount
        leveled_up = False

        while self.experience >= self.level * 100:
            self.experience -= self.level * 100
            self.level += 1
            self.max_hp += 10
            self.max_mp += 5
            self.attack += 2
            self.defense += 1
            self.hp = self.max_hp
            self.mp = self.max_mp
            leveled_up = True

        return leveled_up


def create_character(name: str, character_class: str) -> Character:
    classes = {
        "Wojownik": {
            "max_hp": 140,
            "max_mp": 25,
            "attack": 15,
            "defense": 8,
            "speed": 7,
        },
        "Mag": {
            "max_hp": 85,
            "max_mp": 90,
            "attack": 8,
            "defense": 3,
            "speed": 10,
        },
        "Łotrzyk": {
            "max_hp": 105,
            "max_mp": 45,
            "attack": 12,
            "defense": 5,
            "speed": 15,
        },
    }

    if character_class not in classes:
        raise ValueError("Nieznana klasa postaci.")

    return Character(
        name=name.strip() or "Wędrowiec",
        character_class=character_class,
        **classes[character_class],
    )
