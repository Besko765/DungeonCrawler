
from dataclasses import dataclass


@dataclass
class Enemy:
    name: str
    max_hp: int
    attack: int
    defense: int
    speed: int
    experience_reward: int
    gold_reward: int
    hp: int = 0

    def __post_init__(self):
        if self.hp == 0:
            self.hp = self.max_hp

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, damage: int) -> int:
        actual_damage = max(1, damage - self.defense)
        self.hp = max(0, self.hp - actual_damage)
        return actual_damage


def create_enemy() -> Enemy:
    return Enemy(
        name="Jaskiniowy goblin",
        max_hp=55,
        attack=12,
        defense=3,
        speed=9,
        experience_reward=45,
        gold_reward=15,
    )
