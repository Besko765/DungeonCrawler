
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Header, Footer, Static, Button, Input, Select
)

from models.character import Character, create_character
from models.enemy import create_enemy
from models.item import ItemType
from game.dungeon import Dungeon
from game.combat import Combat,SKILLS

import random
import asyncio

class MainMenuScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="menu", classes="panel"):
            yield Static("D U N G E O N", id="logo")
            yield Static(
                "testowa nazwa",
                id="subtitle",
            )
            yield Button("Nowa gra", id="new_game", variant="primary")
            yield Button("Wyjdź z gry", id="exit", variant="error")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "new_game":
            self.app.push_screen(CharacterCreationScreen())
        elif event.button.id == "exit":
            self.app.exit()


class CharacterCreationScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="creation", classes="panel"):
            yield Static("STWÓRZ BOHATERA", classes="heading")
            yield Static("Imię bohatera:")
            yield Input(
                placeholder="Wpisz imię...",
                value="Wędrowiec",
                id="character_name",
            )
            yield Static("Wybierz klasę:")
            yield Select(
                [
                    ("Wojownik — wytrzymały wojownik", "Wojownik"),
                    ("Mag — potężne zaklęcia", "Mag"),
                    ("Łotrzyk — szybkość i precyzja", "Łotrzyk"),
                ],
                value="Wojownik",
                id="character_class",
            )
            yield Button("Rozpocznij przygodę", id="create", variant="primary")
            yield Button("Powrót", id="cancel")
            yield Static("", id="creation_error")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.app.pop_screen()
            return

        if event.button.id != "create":
            return

        name = self.query_one("#character_name", Input).value.strip()
        character_class = self.query_one("#character_class", Select).value

        if not name:
            self.query_one("#creation_error", Static).update(
                "Wpisz imię bohatera."
            )
            return

        if character_class is Select.BLANK:
            self.query_one("#creation_error", Static).update(
                "Wybierz klasę postaci."
            )
            return

        self.app.start_new_game(name, character_class)
        self.app.push_screen(ExplorationScreen())


class ExplorationScreen(Screen):
    BINDINGS = [
        ("up", "move_up", "Góra"),
        ("down", "move_down", "Dół"),
        ("left", "move_left", "Lewo"),
        ("right", "move_right", "Prawo"),
        ("w", "move_up", "Góra"),
        ("s", "move_down", "Dół"),
        ("a", "move_left", "Lewo"),
        ("d", "move_right", "Prawo"),
        ("e", "interact", "Interakcja"),
        ("i", "inventory", "Ekwipunek"),
        ("escape", "back_to_menu", "Menu"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="game-layout"):
            with Horizontal(id="game-top"):
                with Vertical(id="map-panel", classes="panel"):
                    yield Static("EKSPLORACJA", classes="heading")
                    yield Static("", id="map", markup=True)
                    yield Static(
                        "@ Bohater   M Wróg   C Skrzynia\n"
                        "o Otwarta skrzynia   > Schody\n"
                        "# Ściana   . Podłoga   puste = mgła",
                        id="legend",
                        markup=False,
                    )
                with Vertical(id="stats-panel", classes="panel"):
                    yield Static("BOHATER", classes="heading")
                    yield Static("", id="stats", markup=False)
                    yield Static("STEROWANIE", classes="heading")
                    yield Static(
                        "WASD / strzałki — ruch\n"
                        "E — interakcja\n"
                        "I — ekwipunek\n"
                        "ESC — menu",
                        id="controls",
                    )
            with Vertical(id="bottom-panel", classes="panel"):
                yield Static("DZIENNIK", classes="heading")
                yield Static("", id="log", markup=False)
                yield Button("Ekwipunek", id="inventory")
                yield Button("Powrót do menu", id="back")
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_ui()

    def refresh_ui(self) -> None:
        game = self.app
        player = game.player

        self.query_one("#map", Static).update(
            game.dungeon.render()
        )

        def make_bar(current: int, maximum: int, width: int = 12) -> str:
            if maximum <= 0:
                return "░" * width

            filled = round(width * current / maximum)
            filled = max(0, min(width, filled))

            return "█" * filled + "░" * (width - filled)

        required_exp = player.level * 100

        hp_bar = make_bar(player.hp, player.max_hp)
        mp_bar = make_bar(player.mp, player.max_mp)
        exp_bar = make_bar(player.experience, required_exp)

        weapon_name = player.weapon.name if player.weapon else "Brak"
        armor_name = player.armor.name if player.armor else "Brak"

        self.query_one("#stats", Static).update(
            f"{player.name.upper()}\n"
            f"{player.character_class}  |  Poziom {player.level}\n"
            f"\n"
            f"HP  {hp_bar}\n"
            f"    {player.hp}/{player.max_hp}\n"
            f"\n"
            f"MP  {mp_bar}\n"
            f"    {player.mp}/{player.max_mp}\n"
            f"\n"
            f"EXP {exp_bar}\n"
            f"    {player.experience}/{required_exp}\n"
            f"\n"
            f"ATK  {player.total_attack}\n"
            f"DEF  {player.total_defense}\n"
            f"SPD  {player.speed}\n"
            f"\n"
            f"Złoto: {player.gold}\n"
            f"Broń: {weapon_name}\n"
            f"Zbroja: {armor_name}\n"
            f"\n"
            f"PIĘTRO {game.dungeon.floor}"
        )

        self.query_one("#log", Static).update(game.message)

    def move(self, dx: int, dy: int) -> None:
        game = self.app
        if game.dungeon.move_player(dx, dy):
            game.message = "Przemieszczasz się po lochu."
        else:
            game.message = "Nie można przejść na to pole."
        self.refresh_ui()

    def action_move_up(self) -> None:
        self.move(0, -1)

    def action_move_down(self) -> None:
        self.move(0, 1)

    def action_move_left(self) -> None:
        self.move(-1, 0)

    def action_move_right(self) -> None:
        self.move(1, 0)

    def action_interact(self) -> None:
        game = self.app
        result = game.dungeon.interact()

        if result == "ENEMY":
            enemy_index = game.dungeon.target_enemy_index

            game.combat = Combat(game.player, create_enemy())
            game.combat_enemy_index = enemy_index

            self.app.push_screen(CombatScreen())
            return

        if result == "CHEST_OPENED":
            gold_ammount = random.randrange(1,20)
            game.player.gold += gold_ammount
            game.message = "Otwierasz skrzynię! Zdobywasz " + str(gold_ammount) +" złota."

        elif result == "STAIRS":
            game.dungeon.next_floor()
            game.message = (
                f"Schodzisz na piętro {game.dungeon.floor}. "
                "Przed Tobą kolejny loch."
            )

        else:
            game.message = result

        self.refresh_ui()

    def action_inventory(self) -> None:
        self.app.push_screen(InventoryScreen())

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "inventory":
            self.action_inventory()
        elif event.button.id == "back":
            self.action_back_to_menu()

    def action_back_to_menu(self) -> None:
        self.app.pop_screen()



class SkillSelectionScreen(Screen):
    BINDINGS = [
        ("escape", "go_back", "Powrót"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="skill-layout"):
            yield Static("UMIEJĘTNOŚCI", classes="heading")
            yield Static("", id="skill-description", markup=False)

            with Vertical(id="skill-buttons"):
                pass

            yield Button("Wróć do walki", id="skill-back")
        yield Footer()

    def on_mount(self) -> None:
        player = self.app.player

        if player.character_class == "Mag":
            skills = SKILLS["mag"]
        elif player.character_class == "Łotrzyk":
            skills = SKILLS["lotrzyk"]
        else:
            skills = [
                {
                    "id": "heavy_strike",
                    "name": "Potężne cięcie",
                    "cost": 15,
                    "description": "Zadaje podwójne obrażenia.",
                },
                {
                    "id": "guard",
                    "name": "Postawa obronna",
                    "cost": 10,
                    "description": "Zmniejsza obrażenia z następnego ataku.",
                },
            ]

        self.skills = skills

        for skill in skills:
            self.mount(
                Button(
                    f"{skill['name']} — {skill['cost']} MP",
                    id=f"skill-{skill['id']}",
                )
            )

        self.query_one("#skill-description", Static).update(
            "\n".join(
                f"{skill['name']} ({skill['cost']} MP)\n"
                f"{skill['description']}"
                for skill in skills
            )
        )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "skill-back":
            self.action_go_back()
            return

        skill_id = event.button.id.removeprefix("skill-")
        skill = next(
            (skill for skill in self.skills if skill["id"] == skill_id),
            None,
        )

        if skill is None:
            return

        if self.app.player.mp < skill["cost"]:
            self.query_one("#skill-description", Static).update(
                f"Masz za mało many na {skill['name']}!"
            )
            return

        combat_screen = self.app.screen_stack[-2]
        self.app.pop_screen()
        self.app.call_later(combat_screen.perform_skill, skill)

    def action_go_back(self) -> None:
        self.app.pop_screen()



class CombatScreen(Screen):
    BINDINGS = [
        ("escape", "leave_combat", "Powrót"),
    ]

    def __init__(self):
        super().__init__()
        self.busy = False

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="combat-layout"):
            yield Static("WALKA", classes="heading")

            with Horizontal(id="combat-panels"):
                with Vertical(classes="panel", id="combat-status-panel"):
                    yield Static("STAN WALKI", classes="heading")
                    yield Static("", id="combat_status", markup=False)

                with Vertical(classes="panel", id="combat-log-panel"):
                    yield Static("DZIENNIK WALKI", classes="heading")
                    yield Static("", id="combat_log", markup=False)

            yield Button("Zwykły atak", id="attack", variant="primary")
            yield Button("Umiejętności", id="skill")
            yield Button("Użyj mikstury", id="potion")
            yield Button("Kontynuuj", id="continue", disabled=True)
            yield Button("Wróć do lochu", id="return", disabled=True)
        yield Footer()

    async def on_mount(self) -> None:

        def on_screen_resume(self) -> None:
            self.refresh_ui()

        self.refresh_ui()

        combat = self.app.combat


        if not combat.player_turn and not combat.finished:
            self.busy = True
            self.refresh_ui()
            await asyncio.sleep(0.8)

            message = combat.enemy_turn()
            if message:
                combat.log.append(message)

            combat.player_turn = True
            self.busy = False
            self.refresh_ui()

    def refresh_ui(self) -> None:
        combat = self.app.combat
        player = combat.player
        enemy = combat.enemy

        required_exp = player.level * 100

        self.query_one("#combat_status", Static).update(
            f"{player.name} — {player.character_class}\n"
            f"HP: {player.hp}/{player.max_hp}\n"
            f"MP: {player.mp}/{player.max_mp}\n"
            f"EXP: {player.experience}/{required_exp}\n\n"
            f"{enemy.name}\n"
            f"HP: {enemy.hp}/{enemy.max_hp}\n\n"
            f"Szybkość: {player.speed} vs {enemy.speed}\n"
            f"Status: {'Koniec walki' if combat.finished else 'Tura gracza' if not self.busy else 'Ruch przeciwnika...'}"
        )

        self.query_one("#combat_log", Static).update(
            "\n".join(combat.log[-12:])
        )

        finished = combat.finished

        for button_id in ("attack", "skill", "potion"):
            self.query_one(f"#{button_id}", Button).disabled = (
                finished or self.busy
            )

        self.query_one("#continue", Button).disabled = (
            not finished or not combat.victory
        )
        self.query_one("#return", Button).disabled = not finished

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        combat = self.app.combat

        if event.button.id in ("continue", "return"):
            if not combat.finished:
                return

            if combat.victory:
                enemy_index = self.app.combat_enemy_index
                self.app.dungeon.defeated_enemies.add(enemy_index)
                self.app.combat_enemy_index = None

                self.app.pop_screen()
                self.app.message = (
                    "Zwycięstwo! Możesz kontynuować eksplorację."
                )
            else:
                self.app.pop_screen()
                self.app.push_screen(GameOverScreen())

            return

        if self.busy or combat.finished:
            return

        if event.button.id == "potion":
            self.app.push_screen(PotionScreen())
            return

        if event.button.id == "skill":
            self.app.push_screen(SkillSelectionScreen())
            return

        self.busy = True

        if event.button.id == "attack":
            message = combat.attack()
        else:
            self.busy = False
            return


        self.refresh_ui()


        if not combat.finished:
            await asyncio.sleep(0.8)

            enemy_message = combat.enemy_turn()

            if enemy_message:
                combat.log.append(enemy_message)

        self.busy = False
        self.refresh_ui()

    async def perform_skill(self, skill: dict) -> None:
        combat = self.app.combat

        if self.busy or combat.finished:
            return

        self.busy = True
        self.refresh_ui()

        message = combat.use_skill(skill["name"])



        self.refresh_ui()

        if not combat.finished:
            await asyncio.sleep(0.8)

            enemy_message = combat.enemy_turn()

            if enemy_message:
                combat.log.append(enemy_message)

        self.busy = False
        self.refresh_ui()


    def action_leave_combat(self) -> None:
        if self.app.combat.finished and not self.busy:
            self.app.pop_screen()


class GameOverScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()

        with Vertical(id="game-over-panel", classes="panel"):
            yield Static("KONIEC WYPRAWY", id="game-over-title")
            yield Static("", id="game-over-stats", markup=False)
            yield Button("Nowa wyprawa", id="retry", variant="primary")
            yield Button("Menu główne", id="main-menu")

        yield Footer()

    def on_mount(self) -> None:
        player = self.app.player
        dungeon = self.app.dungeon

        self.query_one("#game-over-stats", Static).update(
            f"Bohater: {player.name}\n"
            f"Klasa: {player.character_class}\n"
            f"Poziom: {player.level}\n"
            f"Zdobyte EXP: {player.experience}\n"
            f"Zebrane złoto: {player.gold}\n"
            f"Osiągnięte piętro: {dungeon.floor}\n\n"
            "Twój bohater poległ w mrocznych lochach."
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "retry":
            player = self.app.player
            self.app.start_new_game(player.name, player.character_class)
            self.app.pop_screen()
            return

        if event.button.id == "main-menu":
            self.app.pop_screen()  # Game Over
            self.app.pop_screen()  # Eksploracja
            self.app.pop_screen()  # Tworzenie postaci




class PotionScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(classes="panel"):
            yield Static("MIKSTURY", classes="heading")
            yield Static("", id="potion_list", markup=False)
            yield Button("Powrót do walki", id="cancel")
            yield Button("Użyj mikstury zdrowia", id="health")
            yield Button("Użyj mikstury many", id="mana")
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_list()

    def refresh_list(self) -> None:
        items = self.app.player.inventory
        potions = [
            f"{i}. {item.name} — {item.description}"
            for i, item in enumerate(items)
            if item.item_type == ItemType.CONSUMABLE
        ]
        self.query_one("#potion_list", Static).update(
            "\n".join(potions) if potions else "Brak mikstur w ekwipunku."
        )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.app.pop_screen()
            return

        target = (
            "Mikstura zdrowia"
            if event.button.id == "health"
            else "Mikstura many"
        )

        inventory = self.app.player.inventory
        index = next(
            (i for i, item in enumerate(inventory) if item.name == target),
            None,
        )

        if index is None:
            self.query_one("#potion_list", Static).update(
                f"Nie masz przedmiotu: {target}."
            )
            return

        combat = self.app.combat
        message = combat.use_potion(index)
        combat.log.append(message)

        if message.startswith("Użyto:") and not combat.finished:
            self.app.pop_screen()
            screen = self.app.screen
            screen.busy = True
            screen.refresh_ui()

            await asyncio.sleep(0.8)

            enemy_message = combat.enemy_turn()
            if enemy_message:
                combat.log.append(enemy_message)

            screen.busy = False
            screen.refresh_ui()
        else:
            self.query_one("#potion_list", Static).update(message)


class InventoryScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(classes="panel"):
            yield Static("EKWIPUNEK", classes="heading")
            yield Static("", id="inventory_list", markup=False)
            yield Input(placeholder="Numer przedmiotu, np. 0", id="item_index")
            yield Button("Załóż przedmiot", id="equip")
            yield Button("Użyj przedmiotu", id="use")
            yield Button("Powrót", id="back")
            yield Static("", id="inventory_message", markup=False)
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_list()

    def refresh_list(self) -> None:
        player = self.app.player
        lines = [
            f"Broń: {player.weapon.name if player.weapon else 'brak'}",
            f"Zbroja: {player.armor.name if player.armor else 'brak'}",
            "",
        ]
        lines.extend(
            f"{i}. {item.name} — {item.description}"
            for i, item in enumerate(player.inventory)
        )
        if not player.inventory:
            lines.append("Ekwipunek jest pusty.")

        self.query_one("#inventory_list", Static).update("\n".join(lines))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
            return

        raw_index = self.query_one("#item_index", Input).value

        try:
            index = int(raw_index)
        except ValueError:
            self.query_one("#inventory_message", Static).update(
                "Wpisz prawidłowy numer przedmiotu."
            )
            return

        player = self.app.player

        if event.button.id == "equip":
            message = player.equip_item(index)
        elif event.button.id == "use":
            message = player.use_item(index)
        else:
            return

        self.query_one("#inventory_message", Static).update(message)
        self.refresh_list()


class Dung(App):
    TITLE = "Dungeon Crawler"
    SUB_TITLE = "DNG"

    CSS = """
    Screen {
        background: #10131b;
        color: #e4e8f0;
    }

    .panel {
        border: round #52627d;
        padding: 1 2;
        margin: 1;
    }

    #menu, #creation {
        width: 60;
        max-width: 90%;
        height: auto;
        align: center middle;
    }

    #logo {
        width: 100%;
        text-align: center;
        color: #e8c981;
        text-style: bold;
        padding: 1;
    }

    #subtitle {
        width: 100%;
        text-align: center;
        color: #9baac4;
        padding: 1;
        margin-bottom: 2;
    }

    #menu Button, #creation Button {
        width: 100%;
        margin-bottom: 1;
    }

    #game-layout {
        height: 1fr;
        padding: 1;
    }

    #game-top {
        height: 1fr;
    }

    #map-panel {
        width: 3fr;
        height: 1fr;
    }

    #map {
        height: 1fr;
        content-align: center middle;
        color: #c5d7f3;
    }

    #stats-panel {
        width: 1fr;
        min-width: 24;
        height: 1fr;
    }

    .heading {
        color: #e8c981;
        text-style: bold;
        margin-bottom: 1;
    }

    #bottom-panel {
        height: auto;
        min-height: 8;
        margin-top: 1;
    }

    #log, #combat_log {
        height: auto;
        min-height: 3;
        margin-bottom: 1;
        color: #c5d7f3;
    }

    #combat-layout {
        width: 70;
        max-width: 95%;
        height: auto;
    }

    #combat-layout Button {
        width: 100%;
        margin-bottom: 1;
    }
    #legend {
    height: 3;
    color: #9baac4;
    margin-top: 1;
    }

    #combat-panels {
        height: 1fr;
        min-height: 12;
    }

    #combat-status-panel {
        width: 1fr;
    }

    #combat-log-panel {
        width: 2fr;
    }

    #combat_log {
        height: 1fr;
        overflow-y: auto;
        color: #c5d7f3;
    }

    #combat_status {
        height: auto;
        color: #e4e8f0;
    }

    #combat-layout {
        height: 1fr;
        padding: 1;
    }

    #combat-layout Button {
        width: 100%;
        margin-bottom: 1;
    }
    
/* Główna przestrzeń gry */
    #game-layout {
        height: 1fr;
        padding: 1;
    }

/* Mapa i panel postaci */
    #game-top {
        height: 1fr;
        min-height: 13;
        layout: horizontal;
    }

    #map-panel {
        width: 1fr;
        min-width: 33;
        height: 1fr;
        border: round #526b8d;
        padding: 1;
    }

    #map {
        width: 100%;
        height: 1fr;
        content-align: center middle;
        color: #c5d7f3;
        text-style: none;
    }

    #stats-panel {
        width: 29;
        min-width: 27;
        height: 1fr;
        border: round #8a7956;
        padding: 1;
    }

    #stats {
        height: 1fr;
        color: #dce4f2;
    }

    #legend {
        height: auto;
        min-height: 3;
        color: #9baac4;
        margin-top: 1;
    }

/* Dziennik zdarzeń */
    #bottom-panel {
        height: auto;
        min-height: 7;
        max-height: 10;
        border: round #52627d;
        padding: 1;
        margin-top: 1;
    }

    #log {
        height: auto;
        min-height: 2;
        color: #c5d7f3;
        margin-bottom: 1;
    }

/* Nagłówki paneli */
    .heading {
        color: #e8c981;
        text-style: bold;
        margin-bottom: 1;
    }
    
    Button {
    text-style: none;
    }
    

    #game-over-panel {
        width: 60;
        max-width: 90%;
        height: auto;
        align: center middle;
        margin: 2;
        padding: 2;
        border: round #8f3947;
    }

    #game-over-title {
        width: 100%;
        text-align: center;
        color: #e05260;
        text-style: bold;
        padding: 2;
    }

    #game-over-stats {
        width: 100%;
        text-align: center;
        padding: 1;
        margin-bottom: 1;
    }

    #game-over-panel Button {
        width: 100%;
        margin-bottom: 1;
    }

    """

    def __init__(self):
        super().__init__()
        self.player: Character | None = None
        self.dungeon = Dungeon()
        self.combat: Combat | None = None
        self.message = "Witaj w Otchłani."

    def on_mount(self) -> None:
        self.push_screen(MainMenuScreen())

    def start_new_game(self, name: str, character_class: str) -> None:
        self.player = create_character(name, character_class)
        self.dungeon = Dungeon()
        self.combat = None
        self.combat_enemy_index = None
        self.message = (
            f"Witaj, {self.player.name}! "
            "Znajdź skrzynię i pokonaj przeciwnika."
        )


if __name__ == "__main__":
    app = Dung()
    app.run()