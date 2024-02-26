import pygame
import random
import enum
from math import sqrt

class MovementDirections(enum.Enum):
    LEFT = 'left'
    RIGHT = 'right'
    UP = 'up'
    DOWN = 'down'


pygame.init()
clock = pygame.time.Clock()

WALL_WIDTH = 40
SCREEN_WIDTH = 19 * WALL_WIDTH
SCREEN_HEIGHT = 19 * WALL_WIDTH

def create_maze(wall_width: int) -> list[pygame.Rect]:
    walls = []
    walls.append(pygame.Rect(0, 0, wall_width, 7*wall_width))
    walls.append(pygame.Rect(0,0,wall_width*19,wall_width))
    walls.append(pygame.Rect(wall_width*2, wall_width*2, wall_width*2, wall_width))
    walls.append(pygame.Rect(wall_width*5, wall_width*2, wall_width*3, wall_width))
    walls.append(pygame.Rect(wall_width*2, wall_width*4, wall_width*2, wall_width))
    walls.append(pygame.Rect(wall_width, wall_width*6, wall_width*3, wall_width))
    walls.append(pygame.Rect(0, wall_width*8, wall_width*4, wall_width))
    walls.append(pygame.Rect(wall_width*3, wall_width*6, wall_width, wall_width*3))
    walls.append(pygame.Rect(wall_width*5, wall_width*4, wall_width, wall_width*5))
    walls.append(pygame.Rect(wall_width*6, wall_width*6, wall_width*2, wall_width))
    walls.append(pygame.Rect(wall_width*9, wall_width, wall_width, wall_width*2))
    walls.append(pygame.Rect(wall_width*7, wall_width*4, wall_width*5, wall_width))
    walls.append(pygame.Rect(wall_width*9, wall_width*5, wall_width, wall_width*2))
    walls.append(pygame.Rect(wall_width*7, wall_width*8, wall_width*3, wall_width))
    walls.append(pygame.Rect(wall_width*7, wall_width*8, wall_width, wall_width*2))

    mirrored_walls = [pygame.Rect(SCREEN_WIDTH - wall.right, wall.top, wall.width, wall.height) for wall in walls]

    all_walls = walls + mirrored_walls

    all_walls += [pygame.Rect(wall.left, SCREEN_HEIGHT - wall.bottom, wall.width, wall.height) for wall in all_walls]

    return all_walls

def draw_maze(maze: list[pygame.Rect], screen: pygame.Surface) -> None:
    for wall in maze:
        pygame.draw.rect(screen, (255, 255, 255), wall)

class Sprite(pygame.Rect):
    maze: list[pygame.Rect]
    direction: MovementDirections
    speed: int
    original_image: pygame.Surface
    screen: pygame.Surface


    def __init__ (self, x: int, y: int, speed: int, original_image: pygame.Surface, maze: list[pygame.Rect], screen: pygame.Surface) -> None:
        super().__init__(x, y, original_image.get_width(), original_image.get_height())
        self.original_image = original_image
        self.maze = maze
        self.screen = screen
        self.direction = random.choice(list(MovementDirections))
        self.speed = speed
        self.IMAGE_ROTATION = {
            MovementDirections.LEFT: pygame.transform.flip(original_image, 1, 0),
            MovementDirections.RIGHT: original_image,
            MovementDirections.UP: pygame.transform.rotate(original_image, 90),
            MovementDirections.DOWN: pygame.transform.rotate(original_image, -90)
            }

    def set_new_sprite_location(self, new_direction: MovementDirections) -> None:
        if new_direction == MovementDirections.LEFT:
            self.x -= self.speed
        elif new_direction == MovementDirections.RIGHT:
            self.x += self.speed
        elif new_direction == MovementDirections.UP:
            self.y -= self.speed
        else:
            self.y += self.speed
        if self.x < 0:
            self.x = SCREEN_WIDTH
        elif self.x > SCREEN_WIDTH:
            self.x = 0

    def __copy__(self):
        new_sprite = Sprite(self.x, self.y, self.speed, self.original_image, self.maze, self.screen)
        new_sprite.direction = self.direction
        new_sprite.IMAGE_ROTATION = self.IMAGE_ROTATION
        return new_sprite
    
    def check_maze_collision(self, new_direction: MovementDirections) -> bool:
        sprite = Sprite(self.x, self.y, self.speed, self.original_image, self.maze, self.screen)
        sprite.set_new_sprite_location(new_direction)
        for wall in self.maze:
            if sprite.colliderect(wall):
                return True
        return False
    
    def make_movement(self, new_direction: MovementDirections) -> bool:
        if not self.check_maze_collision(new_direction):
            self.set_new_sprite_location(new_direction)
            return True
        return False

    def __eq__(self, other) -> bool:
        return self.colliderect(other)
    
    def sprite_update(self) -> None:
        self.screen.blit(self.IMAGE_ROTATION[self.direction], self)
    
class Pacman(Sprite):

    MOVEMENTS = {
        pygame.K_LEFT: MovementDirections.LEFT,
        pygame.K_RIGHT: MovementDirections.RIGHT,
        pygame.K_UP: MovementDirections.UP,
        pygame.K_DOWN: MovementDirections.DOWN
                 }

    def make_pacman_movement(self, keys: pygame.key.ScancodeWrapper):
        for key, value in self.MOVEMENTS.items():
            if keys[key]:
                self.direction = value
                self.make_movement(self.direction) 

class Ghost(Sprite):
    hero: Pacman
    def __init__(self, x: int, y: int, speed: int, original_image: pygame.Surface, 
                 maze: list[pygame.Rect], screen: pygame.Surface, hero: Pacman) -> None:

        super().__init__(x, y, speed, original_image, maze, screen)
        self.hero = hero

    def get_hero_distnance(self) -> float:
        x_difference = self.x - self.hero.x
        y_difference = self.y - self.hero.y
        return sqrt(x_difference ** 2 + y_difference ** 2)
    
    def make_ghost_movement(self) -> None:
        directions = {
            MovementDirections.LEFT: ([MovementDirections.LEFT, MovementDirections.UP, MovementDirections.DOWN], MovementDirections.RIGHT),
            MovementDirections.RIGHT: ([MovementDirections.RIGHT, MovementDirections.UP, MovementDirections.DOWN], MovementDirections.LEFT),
            MovementDirections.UP: ([MovementDirections.LEFT, MovementDirections.RIGHT, MovementDirections.UP], MovementDirections.DOWN),
            MovementDirections.DOWN: ([MovementDirections.LEFT, MovementDirections.RIGHT, MovementDirections.DOWN], MovementDirections.UP)
            }
        
        valid_directions = []
        new_directions, back_direction = directions[self.direction]

        for direction in new_directions:
            if not self.check_maze_collision(direction):
                valid_directions.append(direction)

        hero_proximity = {}

        if len(valid_directions) > 0:
            for direction in valid_directions:
                hero_proximity[direction] = self.get_hero_distnance() - random.random()
                self.direction = min(hero_proximity, key=lambda x: hero_proximity[x])
        else:
            self.direction = back_direction
        
        self.make_movement(self.direction)

    def catch_hero(self) -> bool:
        return self == self.hero

    
    


def main() -> None:
    
    pacman = pygame.display.set_mode((SCREEN_HEIGHT, SCREEN_WIDTH))
    pygame.display.set_caption('Pacman')

    maze = create_maze(WALL_WIDTH)
    draw_maze(maze, pacman)

    hero_speed = 4
    enemy_speed = 3

    enemies = []

    hero = Pacman(WALL_WIDTH, WALL_WIDTH*9+1, hero_speed, pygame.image.load('pacman.png'), maze, pacman)
    enemies.append(Ghost(WALL_WIDTH*17, WALL_WIDTH*9+1, enemy_speed, pygame.image.load('ghost_1.png'), maze, pacman, hero))
    enemies.append(Ghost(WALL_WIDTH*17+1, WALL_WIDTH+1, enemy_speed+2, pygame.image.load('ghost_2.png'), maze, pacman, hero))

    
    hero.sprite_update()
    for enemy in enemies: enemy.sprite_update()

    pygame.display.flip()
    pygame.display.update()

    font = pygame.font.Font(None, 36)

    while 1:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()

        keys = pygame.key.get_pressed()
        hero.make_pacman_movement(keys)

        for enemy in enemies:
            enemy.make_ghost_movement()

            if enemy.catch_hero():
        
                game_over_text = font.render("GAME OVER", True, (255, 255, 255))
                pacman.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, SCREEN_HEIGHT // 2 - game_over_text.get_height() // 2))
                pygame.display.flip()
                # while 1:
                #     for event in pygame.event.get():
                #         if event.type == pygame.QUIT:
                #             exit()

        pygame.display.flip()

        pacman.fill((0,0,0))
        draw_maze(maze, pacman)
        for enemy in enemies: enemy.sprite_update()
        hero.sprite_update()        
        pygame.display.update()

        clock.tick(60)

main()

