
from dataclasses import dataclass
from enum import Enum


class ItemType(Enum):
    CONSUMABLE = "consumable"
    WEAPON = "weapon"
    ARMOR = "armor"


@dataclass
class Item:
    name: str
    description: str
    item_type: ItemType
    value: int
    drop_chance: float = 0.0

    def __str__(self) -> str:
        return self.name


HEALTH_POTION = Item(
    name="Mikstura zdrowia",
    description="Przywraca 40 HP.",
    item_type=ItemType.CONSUMABLE,
    value=40,
    drop_chance=0.45,
)

MANA_POTION = Item(
    name="Mikstura many",
    description="Przywraca 25 MP.",
    item_type=ItemType.CONSUMABLE,
    value=25,
    drop_chance=0.30,
)

IRON_SWORD = Item(
    name="Żelazny miecz",
    description="Zwiększa atak o 5.",
    item_type=ItemType.WEAPON,
    value=5,
    drop_chance=0.15,
)

LEATHER_ARMOR = Item(
    name="Skórzana zbroja",
    description="Zwiększa obronę o 2.",
    item_type=ItemType.ARMOR,
    value=2,
    drop_chance=0.10,
)


ALL_ITEMS = [
    HEALTH_POTION,
    MANA_POTION,
    IRON_SWORD,
    LEATHER_ARMOR,
]
