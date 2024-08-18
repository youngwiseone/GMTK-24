import pygame
import sys

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
TILE_SIZE = 32
ROWS = SCREEN_HEIGHT // TILE_SIZE
COLS = SCREEN_WIDTH // TILE_SIZE
LOG_HEALTH = 100
LEVEL = 1
STARTING_RESOURCES = 0

# Set up the display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Build to Sail - Raft Game")

pygame.mixer.init()

# Load sounds
log_break_sound = pygame.mixer.Sound("Assets/Sounds/log_break.wav")
barrel_select_sound = pygame.mixer.Sound("Assets/Sounds/barrel_select.wav")
player_move_sound = pygame.mixer.Sound("Assets/Sounds/slime_jump.wav")
player_move_sound.set_volume(0.1)
pygame.mixer.music.load("Assets/Sounds/background_music.wav")
pygame.mixer.music.set_volume(0.2)
pygame.mixer.music.play(-1)

# Load images from the Assets folder
background_tile = pygame.image.load("Assets/sea.png").convert()
log_back_tile = pygame.image.load("Assets/log_back.png").convert()
log_middle_tile = pygame.image.load("Assets/log_middle.png").convert()
log_front_tile = pygame.image.load("Assets/log_front.png").convert()
player_image = pygame.image.load("Assets/slime.png").convert()
wood_tile = pygame.image.load("Assets/wood.png").convert()
metal_tile = pygame.image.load("Assets/metal.png").convert()
barrel_tile = pygame.image.load("Assets/barrel.png").convert()
add_tile = pygame.image.load("Assets/add.png").convert()

# Chroma key: make black (0, 0, 0) transparent
log_back_tile.set_colorkey((0, 0, 0))
log_middle_tile.set_colorkey((0, 0, 0))
log_front_tile.set_colorkey((0, 0, 0))
player_image.set_colorkey((0, 0, 0))
wood_tile.set_colorkey((0, 0, 0))
metal_tile.set_colorkey((0, 0, 0))
barrel_tile.set_colorkey((0, 0, 0))
add_tile.set_colorkey((0, 0, 0))

# Resources
class Resource:
    def __init__(self, type, x, y, current_stock, max_stock, sprite):
        self.type = type
        self.x = x
        self.y = y
        self.current_stock = current_stock
        self.max_stock = max_stock
        self.sprite = sprite

    def draw(self):
        # Draw the sprite
        screen.blit(self.sprite, (self.x, self.y))

        # Draw the resource count above the resource
        font = pygame.font.SysFont(None, 24)
        resource_text = font.render(f"{self.current_stock}/{self.max_stock}", True, (255, 255, 255))
        screen.blit(resource_text, (self.x, self.y + TILE_SIZE))
    
    def add_stock(self, amount):
        self.current_stock = min(self.current_stock + amount, self.max_stock)

    def remove_stock(self, amount):
        self.current_stock = max(self.current_stock - amount, 0)


# Log class to handle each log object
class Log:
    def __init__(self, x, y, level):
        self.x = x
        self.y = y
        self.level = level
        self.health = LOG_HEALTH * self.level
        self.has_empty_spot = True

    def draw(self, player):
        # Place log_back.png at the top
        screen.blit(log_back_tile, (self.x, self.y - TILE_SIZE))
        # Place log_middle.png in the middle
        screen.blit(log_middle_tile, (self.x, self.y))
        # Place log_front.png at the bottom
        screen.blit(log_front_tile, (self.x, self.y + TILE_SIZE))

        # Draw the health bar above the log
        font = pygame.font.SysFont(None, 24)
        health_text = font.render(str(self.health), True, (255, 255, 255))
        screen.blit(health_text, (self.x, self.y - TILE_SIZE * 2))

        # Only draw the add_tile if this is the log the player is on and it has an empty spot
        if self.has_empty_spot and self.x == player.x and self.y == player.y:
            screen.blit(add_tile, (self.x, self.y - TILE_SIZE))

    def update(self, logs):
        # Check if there are logs on both sides
        has_left_log = any(log.x == self.x - TILE_SIZE and log.y == self.y for log in logs)
        has_right_log = any(log.x == self.x + TILE_SIZE and log.y == self.y for log in logs)
    
        # Only decrease health if there isn't a log on both sides
        if not (has_left_log and has_right_log):
            self.health -= 1

        # Ensure health doesn't go below 0
        if self.health < 0:
            self.health = 0

    def restore_health(self, amount):
        self.health += amount

    def is_destroyed(self):
        # Check if the log is destroyed (health reaches 0)
        return self.health == 0
    
# Bobber class to handle the bobber object
class Bobber:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.image = pygame.image.load("Assets/bobber_dunk6.png").convert_alpha()

    def draw(self):
        screen.blit(self.image, (self.x, self.y))

# Player class to handle the player object
class Player:
    def __init__(self, x, y):
        self.image = player_image
        self.x = x
        self.y = y
        self.target_x = None
        self.start_x = None
        self.progress = 0
        self.speed = 0.4  # Speed attribute for sliding
        self.bobber = None  # Bobber attribute

        # Load animation frames
        self.sliding_frames = [
            pygame.image.load(f"Assets/slime_jump{i}.png").convert_alpha()
            for i in range(1, 8)
        ]
        self.current_frame = 0
        self.frame_count = len(self.sliding_frames)

        # Load fishing animation frames
        self.fishing_frames = [
            pygame.image.load(f"Assets/slime_fishing{i}.png").convert_alpha()
            for i in range(1, 7)
        ]
        self.is_fishing = False

    def move(self, direction, logs):
        # If the player is fishing, reset the animation and stop fishing
        if self.is_fishing:
            self.is_fishing = False
            self.current_frame = 0

        # Calculate the new position
        if direction == "left":
            new_x = self.x - TILE_SIZE
        elif direction == "right":
            new_x = self.x + TILE_SIZE
        else:
            return

        # Check if there is a log at the new position
        if self.can_stand_on_log(new_x, logs):
            self.start_x = self.x  # Record the starting x position
            self.target_x = new_x  # Set the target x position
            self.progress = 0

    def can_stand_on_log(self, x, logs):
        # Check if there is a log at the given x coordinate and current y
        for log in logs:
            if log.x == x and log.y == self.y and not log.is_destroyed():
                return True
        return False

    def update(self, logs):
        # Perform sliding if there is a target position
        if self.target_x is not None:
            self.perform_slide()
            return
        
        # Perform fishing animation if fishing
        if self.is_fishing:
            self.perform_fishing()

        # Check if the log the player is standing on is destroyed
        if not self.can_stand_on_log(self.x, logs):
            # If the player is fishing, reset the animation and stop fishing
            self.current_frame = 0
            # Make the player fall down one tile space
            self.y += TILE_SIZE
            # If the player is no longer on a log, delete the player
            if not self.can_stand_on_log(self.x, logs):
                return True
            
        return False
    
    def start_slide(self, target_x):
        # Initiates the slide animation.
        self.sliding = True
        self.slide_target_x = target_x
        self.slide_start_x = self.x
        self.slide_progress = 0

    def perform_slide(self):
        if self.target_x is None:
            return
        self.bobber = False
        self.progress += self.speed  # Increase progress based on speed

        # Apply easing (quadratic easing)
        easing_progress = self.ease_in_out(self.progress)

        # Interpolate the x position
        self.x = self.start_x + (self.target_x - self.start_x) * easing_progress
        
        # Update the calculation of the current animation frame in the perform_slide method
        self.current_frame = int(self.progress * self.frame_count) % self.frame_count

        # End the slide when progress is complete
        if self.progress >= 1:
            self.x = self.target_x
            self.target_x = None
            self.current_frame = 0

    def perform_fishing(self):
        # Update the current frame based on fishing animation
        self.current_frame += 1
        if self.current_frame >= len(self.fishing_frames):
            self.current_frame = len(self.fishing_frames) - 1  # Stay on the last frame

            # After the animation is done, add the resources
            # self.complete_fishing()

    def complete_fishing(self):
        # Add resources after completing the fishing animation
        wood.add_stock(5)  # Add 5 wood to the current stock
        self.is_fishing = False  # Stop fishing after resources are added
        self.current_frame = 0

    def start_fishing(self):
        # Start the fishing animation
        self.is_fishing = True
        self.current_frame = 0
        self.bobber = Bobber(self.x, self.y + 2 * TILE_SIZE)  # Spawn bobber 2 tiles below the player

    def ease_in_out(self, t):
        return 3 * t**2 - 2 * t**3  # Smooth start and end

    def draw(self):
        if self.is_fishing:
            frame_image = self.fishing_frames[self.current_frame]
        else:
            frame_image = self.sliding_frames[self.current_frame]
        screen.blit(frame_image, (self.x, self.y - TILE_SIZE))

        # Draw the bobber if it exists
        if self.bobber:
            self.bobber.draw()


class Barrel:
    def __init__(self, x, y, sprite, log, resource_type):
        self.x = x
        self.y = y
        self.log = log 
        self.sprite = sprite
        self.resource_type = resource_type

    def draw(self):
        screen.blit(self.sprite, (self.x, self.y))
        # Draw the resource tile on the barrel
        if self.resource_type == "wood":
            resource_sprite = wood_tile
        elif self.resource_type == "metal":
            resource_sprite = metal_tile
        else:
            resource_sprite = None

        if resource_sprite:
            screen.blit(resource_sprite, (self.x, self.y))

def show_resource_selection_menu():
    # Draw the menu background
    menu_width, menu_height = 200, 150
    menu_x = SCREEN_WIDTH // 2 - menu_width // 2
    menu_y = SCREEN_HEIGHT // 2 - menu_height // 2
    pygame.draw.rect(screen, (0, 0, 0), (menu_x, menu_y, menu_width, menu_height))

    # Draw the options
    font = pygame.font.SysFont(None, 24)
    wood_option = font.render("Add 50 to Wood Max", True, (255, 255, 255))
    metal_option = font.render("Add 50 to Metal Max", True, (255, 255, 255))
    
    screen.blit(wood_option, (menu_x + 20, menu_y + 20))
    screen.blit(metal_option, (menu_x + 20, menu_y + 60))

    # Refresh display to show the menu
    pygame.display.flip()

    # Wait for player to select an option
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos
                if menu_x < mouse_x < menu_x + menu_width:
                    if menu_y < mouse_y < menu_y + 40:
                        return "wood"
                    elif menu_y + 40 < mouse_y < menu_y + 80:
                        return "metal"

# Main game loop
running = True
logs = []
barrels = []
# Initialize background tiles
# Load images for background animation
background_frames = [
    pygame.image.load(f"Assets/sea_animation{i}.png").convert()
    for i in range(1, 5)
]
current_background_frame = 0
background_frame_count = len(background_frames)
background_animation_speed = 2  # Adjust this for desired speed
background_frame_timer = 0
background_tiles = []

# Fill the screen with the initial background tiles
for row in range(ROWS):
    for col in range(COLS):
        background_tiles.append(pygame.Rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE))

background_speed = 2  # Speed at which the background moves
background_moving = True  # Track if the background is moving

# Create resources
wood = Resource("wood", SCREEN_WIDTH // 2 - TILE_SIZE, TILE_SIZE, STARTING_RESOURCES, 100, wood_tile)
metal = Resource("metal", SCREEN_WIDTH // 2 + TILE_SIZE, TILE_SIZE, STARTING_RESOURCES, 100, metal_tile)

# Create and add 3 logs spaced horizontally
logs.append(Log(center_x := (COLS // 2) * TILE_SIZE, center_y := (ROWS // 2) * TILE_SIZE, 4))
logs.append(Log(center_x + TILE_SIZE, center_y, 2))
logs.append(Log(center_x - TILE_SIZE, center_y, 1))

# Create the player and place it on the first log
player = Player(center_x, center_y - TILE_SIZE)

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                player.move("left", logs)
                player_move_sound.play()
            elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                player.move("right", logs)
                player_move_sound.play()
            elif event.key == pygame.K_f:
                player.start_fishing()
            elif event.key == pygame.K_SPACE:
                # Check if the player is on a log and has enough wood
                for log in logs:
                    if log.x == player.x:
                        if wood.current_stock >= 5:
                            wood.remove_stock(5)  # Use 5 wood
                            log.restore_health(50)  # Restore 50 health to the log
            elif event.key == pygame.K_e:
                # Check if the player has at least 10 wood
                if wood.current_stock >= 10:
                    # Determine if there is space to the left or right of the current log
                    can_build_left = not any(log.x == player.x - TILE_SIZE for log in logs)
                    can_build_right = not any(log.x == player.x + TILE_SIZE for log in logs)

                    # Build the log if there is space
                    if can_build_left or can_build_right:
                        wood.remove_stock(10)  # Subtract 10 wood from the stock

                        if can_build_left:
                            logs.append(Log(player.x - TILE_SIZE, player.y, 1))
                        elif can_build_right:
                            logs.append(Log(player.x + TILE_SIZE, player.y, 1))
        # Separate MOUSEBUTTONDOWN handling
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            for log in logs:
                # Check if the click is on the add_tile and the log has an empty spot
                if log.has_empty_spot and log.x <= mouse_x <= log.x + TILE_SIZE and log.y - TILE_SIZE <= mouse_y <= log.y:
                    if log.x == player.x and log.y == player.y:  # Ensure the player is on the log
                        # Show the resource selection menu
                        selected_resource = show_resource_selection_menu()

                        # Place the barrel on the log with the selected resource type
                        barrels.append(Barrel(log.x, log.y - TILE_SIZE, barrel_tile, log, selected_resource))
                        log.has_empty_spot = False  # Mark the spot as used
                        barrel_select_sound.play()

                        # Increase the max limit of the selected resource
                        if selected_resource == "wood":
                            wood.max_stock += 50
                        elif selected_resource == "metal":
                            metal.max_stock += 50

                        break

    # Update background animation
    background_frame_timer += 1
    if background_frame_timer >= background_animation_speed:
        current_background_frame = (current_background_frame + 1) % background_frame_count
        background_frame_timer = 0
    
    # Move background tiles
    if background_moving:
        for tile in background_tiles:
            tile.x -= background_speed

        # Remove tiles that move off the screen
        background_tiles = [tile for tile in background_tiles if tile.x + TILE_SIZE > 0]

        # Spawn new tiles on the right side
        last_col_x = max(tile.x for tile in background_tiles) + TILE_SIZE
        if len([tile for tile in background_tiles if tile.x == last_col_x]) < ROWS:
            for row in range(ROWS):
                background_tiles.append(pygame.Rect(last_col_x, row * TILE_SIZE, TILE_SIZE, TILE_SIZE))

    # Draw the background tiles with the current frame
    for tile in background_tiles:
        screen.blit(background_frames[current_background_frame], tile)

    # Draw the resource
    wood.draw()
    metal.draw()

    # Update and draw all logs
    for log in logs[:]:
        log.update(logs)
        log.draw(player)
        if log.is_destroyed():
            logs.remove(log)
            log_break_sound.play()  # Play the sound when the log is removed
            # Remove any barrels on this log and reduce the resource max
            for barrel in barrels[:]:
                if barrel.log == log:
                    if barrel.resource_type == "wood":
                        wood.max_stock -= 50  # Decrease the max stock of wood by 50
                    if barrel.resource_type == "metal":
                        metal.max_stock -= 50  # Decrease the max stock of wood by 50
                    barrels.remove(barrel)

    # Draw all barrels
    for barrel in barrels:
        barrel.draw()


    # Update and draw the player
    if player.update(logs):
        player = None  # Delete the player if they fall off the log
    if player:
        player.draw()

    # Update the display
    pygame.display.flip()

    # Control the frame rate
    pygame.time.delay(100)  # Delay to slow down health decrease

# Quit Pygame
pygame.quit()
sys.exit()