
import random


class Dungeon:
    WIDTH = 50
    HEIGHT = 22
    ROOM_ATTEMPTS = 35
    VIEW_RADIUS = 5
    VIEW_WIDTH = 31
    VIEW_HEIGHT = 13

    def __init__(self):
        self.floor = 1
        self.generate_floor()

    def generate_floor(self):
        self.grid = [
            ["#" for _ in range(self.WIDTH)]
            for _ in range(self.HEIGHT)
        ]

        self.rooms = []

        for _ in range(self.ROOM_ATTEMPTS):
            width = random.randint(5, 10)
            height = random.randint(4, 7)
            x = random.randint(1, self.WIDTH - width - 2)
            y = random.randint(1, self.HEIGHT - height - 2)

            room = (x, y, width, height)

            if any(self.rooms_overlap(room, other) for other in self.rooms):
                continue

            self.rooms.append(room)
            self.carve_room(room)

        if not self.rooms:
            self.rooms = [(2, 2, 8, 6), (20, 8, 8, 6)]
            for room in self.rooms:
                self.carve_room(room)

        for index in range(1, len(self.rooms)):
            previous = self.room_center(self.rooms[index - 1])
            current = self.room_center(self.rooms[index])
            self.carve_corridor(previous, current)


        start = self.room_center(self.rooms[0])
        self.player_position = start

        occupied = {start}

        self.chest_position = self.random_room_position(
            self.rooms[0], occupied
        )
        occupied.add(self.chest_position)

        final_room = self.rooms[-1]
        self.stairs_position = self.random_room_position(
            final_room, occupied
        )
        occupied.add(self.stairs_position)


        self.enemy_positions = []
        self.defeated_enemies = set()
        self.target_enemy_index = None

        enemy_count = random.randint(2, 6)

        for _ in range(enemy_count):
            available_rooms = [
                room for room in self.rooms
                if any(
                    self.grid[y][x] == "."
                    and (x, y) not in occupied
                    for y in range(room[1], room[1] + room[3])
                    for x in range(room[0], room[0] + room[2])
                )
            ]

            if not available_rooms:
                break

            room = random.choice(available_rooms)
            position = self.random_room_position(room, occupied)

            self.enemy_positions.append(position)
            occupied.add(position)

        self.chest_opened = False
        self.explored = set()
        self.update_visibility()


    @staticmethod
    def rooms_overlap(a, b):
        ax, ay, aw, ah = a
        bx, by, bw, bh = b

        return (
            ax - 1 < bx + bw
            and ax + aw + 1 > bx
            and ay - 1 < by + bh
            and ay + ah + 1 > by
        )

    def carve_room(self, room):
        x, y, width, height = room

        for row in range(y, y + height):
            for col in range(x, x + width):
                self.grid[row][col] = "."

    def carve_corridor(self, start, end):
        x1, y1 = start
        x2, y2 = end

        if random.choice([True, False]):
            self.carve_horizontal(x1, x2, y1)
            self.carve_vertical(y1, y2, x2)
        else:
            self.carve_vertical(y1, y2, x1)
            self.carve_horizontal(x1, x2, y2)

    def carve_horizontal(self, x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.grid[y][x] = "."

    def carve_vertical(self, y1, y2, x):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.grid[y][x] = "."

    @staticmethod
    def room_center(room):
        x, y, width, height = room
        return x + width // 2, y + height // 2

    def random_room_position(self, room, occupied):
        x, y, width, height = room

        candidates = [
            (px, py)
            for py in range(y, y + height)
            for px in range(x, x + width)
            if self.grid[py][px] == "."
            and (px, py) not in occupied
        ]

        if candidates:
            return random.choice(candidates)


        candidates = [
            (px, py)
            for py in range(1, self.HEIGHT - 1)
            for px in range(1, self.WIDTH - 1)
            if self.grid[py][px] == "."
            and (px, py) not in occupied
        ]

        return random.choice(candidates)

    def update_visibility(self):
        px, py = self.player_position

        for y in range(max(0, py - self.VIEW_RADIUS),
                       min(self.HEIGHT, py + self.VIEW_RADIUS + 1)):
            for x in range(max(0, px - self.VIEW_RADIUS),
                           min(self.WIDTH, px + self.VIEW_RADIUS + 1)):
                if abs(px - x) + abs(py - y) <= self.VIEW_RADIUS:
                    self.explored.add((x, y))

    def move_player(self, dx, dy):
        x, y = self.player_position
        nx, ny = x + dx, y + dy

        if not (0 <= nx < self.WIDTH and 0 <= ny < self.HEIGHT):
            return False

        if self.grid[ny][nx] == "#":
            return False

        new_position = (nx, ny)

        if (
            new_position == self.chest_position
            and not self.chest_opened
        ):
            return False

        if any(
                position == new_position
                and index not in self.defeated_enemies
                for index, position in enumerate(self.enemy_positions)
        ):
            return False

        self.player_position = new_position
        self.update_visibility()
        return True

    def interact(self):
        px, py = self.player_position

        def adjacent(position):
            x, y = position
            return abs(px - x) + abs(py - y) == 1

        for index, position in enumerate(self.enemy_positions):
            if (
                    index not in self.defeated_enemies
                    and adjacent(position)
            ):
                self.target_enemy_index = index
                return "ENEMY"

        if adjacent(self.chest_position):
            if self.chest_opened:
                return "Skrzynia jest już pusta."

            self.chest_opened = True
            return "CHEST_OPENED"

        if adjacent(self.stairs_position):
            return "STAIRS"

        return "Podejdź bliżej do skrzyni, przeciwnika lub schodów."

    def next_floor(self):
        self.floor += 1
        self.generate_floor()

    def render(self):
        px, py = self.player_position

        # Kamera chodzi z bohaterem
        camera_x = max(
            0,
            min(
                px - self.VIEW_WIDTH // 2,
                self.WIDTH - self.VIEW_WIDTH,
            ),
        )

        camera_y = max(
            0,
            min(
                py - self.VIEW_HEIGHT // 2,
                self.HEIGHT - self.VIEW_HEIGHT,
            ),
        )

        rows = []

        for y in range(camera_y, camera_y + self.VIEW_HEIGHT):
            row = []

            for x in range(camera_x, camera_x + self.VIEW_WIDTH):
                position = (x, y)
                distance = abs(px - x) + abs(py - y)


                if position == self.player_position:
                    symbol = "@"
                elif position not in self.explored:
                    row.append(" ")
                    continue
                elif(
                    position in self.enemy_positions
                    and self.enemy_positions.index(position)
                    not in self.defeated_enemies
                    and distance <= self.VIEW_RADIUS
                ) :
                    symbol = "[red bold]M[/red bold]"
                elif position == self.chest_position:
                    symbol = "o" if self.chest_opened else "C"
                elif position == self.stairs_position:
                    symbol = ">"
                else:
                    symbol = self.grid[y][x]

                row.append(symbol)

            rows.append("".join(row))

        return "\n".join(rows)

