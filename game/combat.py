
import random

from models.character import Character
from models.enemy import Enemy
from models.item import ALL_ITEMS


SKILLS = {
    "mag": [
        {
            "id": "fireball",
            "name": "Kula ognia",
            "cost": 15,
            "description": "Silne obrażenia magiczne.",
        },
        {
            "id": "ice_lance",
            "name": "Lodowa lanca",
            "cost": 18,
            "description": "Obrażenia i osłabienie ataku wroga.",
        },
        {
            "id": "lightning",
            "name": "Łańcuch błyskawic",
            "cost": 25,
            "description": "Potężne obrażenia magiczne.",
        },
        {
            "id": "regeneration",
            "name": "Regeneracja",
            "cost": 20,
            "description": "Przywraca część HP.",
        },
    ],
    "lotrzyk": [
        {
            "id": "weak_point",
            "name": "Cios w słaby punkt",
            "cost": 12,
            "description": "Zadaje duże obrażenia.",
        },
        {
            "id": "poison",
            "name": "Zatrute ostrze",
            "cost": 16,
            "description": "Atak z efektem trucizny.",
        },
        {
            "id": "flurry",
            "name": "Grad cięć",
            "cost": 20,
            "description": "Wykonuje trzy szybkie uderzenia.",
        },
        {
            "id": "dodge",
            "name": "Unik",
            "cost": 10,
            "description": "Zmniejsza obrażenia z następnego ataku.",
        },
    ],
}



class Combat:
    def __init__(self, player: Character, enemy: Enemy):
        self.player = player
        self.enemy = enemy
        self.finished = False
        self.victory = False

        self.log: list[str] = [
            f"Rozpoczyna się walka z {enemy.name}."
        ]

        self.player_turn = player.speed >= enemy.speed

        if not self.player_turn:
            self.log.append(
                f"{enemy.name} jest szybszy i zaatakuje pierwszy!"
            )

    def attack(self) -> str:
        if self.finished:
            return "Walka jest zakończona."

        damage = random.randint(
            max(1, self.player.total_attack - 3),
            self.player.total_attack + 3,
        )

        actual = self.enemy.take_damage(damage)
        message = f"{self.player.name} zadaje {actual} obrażeń."
        self.log.append(message)

        if not self.enemy.is_alive:
            self._win()

        return message

    def use_skill(self, skill_name: str | None = None) -> str:
        if self.finished:
            return "Walka jest zakończona."

        cost = 15

        if self.player.mp < cost:
            return "Masz za mało many."

        self.player.mp -= cost

        if self.player.character_class == "Wojownik":
            damage = self.player.total_attack * 2
            default_name = "Potężne cięcie"
        elif self.player.character_class == "Mag":
            damage = self.player.total_attack * 2 + 12
            default_name = "Kula ognia"
        else:
            damage = self.player.total_attack + 10
            default_name = "Cios w słaby punkt"

        actual = self.enemy.take_damage(damage)
        used_name = skill_name or default_name

        message = (
            f"{used_name} zadaje {actual} obrażeń. "
            f"Zużyto {cost} MP."
        )

        self.log.append(message)

        if not self.enemy.is_alive:
            self._win()

        return message

    def enemy_turn(self) -> str:
        if self.finished or not self.enemy.is_alive:
            return ""

        damage = random.randint(
            max(1, self.enemy.attack - 3),
            self.enemy.attack + 3,
        )

        actual = self.player.take_damage(damage)
        message = f"{self.enemy.name} zadaje Ci {actual} obrażeń."

        if not self.player.is_alive:
            self.finished = True
            self.victory = False
            self.log.append("Zostałeś pokonany.")

        return message

    def use_potion(self, inventory_index: int) -> str:
        if self.finished:
            return "Walka jest zakończona."

        return self.player.use_item(inventory_index)

    def _win(self) -> None:
        if self.finished:
            return

        self.finished = True
        self.victory = True

        self.player.gold += self.enemy.gold_reward

        leveled_up = self.player.gain_experience(
            self.enemy.experience_reward
        )

        self.log.append(
            f"Zwycięstwo! +{self.enemy.experience_reward} EXP, "
            f"+{self.enemy.gold_reward} złota."
        )

        if leveled_up:
            self.log.append(
                f"AWANS! Osiągasz poziom {self.player.level}. "
                "Twoje HP i MP zostały w pełni odnowione!"
            )

        dropped_item = self._roll_drop()

        if dropped_item:
            self.player.add_item(dropped_item)
            self.log.append(
                f"Łup: {dropped_item.name} — "
                f"{dropped_item.description}"
            )
        else:
            self.log.append("Tym razem przeciwnik nic nie upuścił.")

    @staticmethod
    def _roll_drop():
        if random.random() > 0.65:
            return None

        weights = [item.drop_chance for item in ALL_ITEMS]

        return random.choices(
            ALL_ITEMS,
            weights=weights,
            k=1,
        )[0]
