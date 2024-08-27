import pygame
import sys
import random
import time

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
STARTING_RESOURCES = 100
METER_DISTANCE_PER_KNOT = 32

menu_font = pygame.font.SysFont(None, 40)  # Adjust size as needed
menu_x = SCREEN_WIDTH // 2 - 160  # Center the menu horizontally
menu_y = -320  # Start above the screen
menu_falling = False  # Track if the menu is falling
menu_landed = False  # Track if the menu has landed
menu_fall_speed = 80  # Speed of the menu falling

sea_level = 0  # Initialize sea level
knots_speed = 0  # Initial speed
distance_travelled = 0  # Distance travelled in meters
distance_meter = 0  # Used to accumulate knot distance until a meter is achieved

# Set up the display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Build to Sail - Raft Game")

pygame.mixer.init()

# Load sounds
log_break_sound = pygame.mixer.Sound("Assets/Sounds/log_break.wav")
barrel_select_sound = pygame.mixer.Sound("Assets/Sounds/barrel_select.wav")
player_move_sound = pygame.mixer.Sound("Assets/Sounds/slime_jump.wav")
cast_line_sound = pygame.mixer.Sound("Assets/Sounds/cast_line.wav")
bobber_lands_sound = pygame.mixer.Sound("Assets/Sounds/bobber_lands.wav")
fish_on_line_sound = pygame.mixer.Sound("Assets/Sounds/fish_on_line.wav")
game_over_sound = pygame.mixer.Sound("Assets/Sounds/game_over.wav")
player_move_sound.set_volume(0.1)
fish_on_line_sound.set_volume(1.3)
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
menu_image = pygame.image.load("Assets/menu.png").convert()
water_splash_tile = pygame.image.load("Assets/water_splash.png").convert()
auto_fisher_tile = pygame.image.load("Assets/autofishin.png").convert()
repairer_tile = pygame.image.load("Assets/Animations/Repairer/repairer1.png").convert()

#Load log images
log_back_images = [
    pygame.image.load("Assets/Animations/Logs/log_back1.png").convert_alpha(),  # 100%-80%
    pygame.image.load("Assets/Animations/Logs/log_back2.png").convert_alpha(),  # 80%-60%
    pygame.image.load("Assets/Animations/Logs/log_back3.png").convert_alpha(),  # 60%-40%
    pygame.image.load("Assets/Animations/Logs/log_back4.png").convert_alpha(),  # 40%-20%
    pygame.image.load("Assets/Animations/Logs/log_back5.png").convert_alpha()   # 20%-0%
]
log_middle_images = [
    pygame.image.load("Assets/Animations/Logs/log_middle1.png").convert_alpha(),  # 100%-80%
    pygame.image.load("Assets/Animations/Logs/log_middle2.png").convert_alpha(),  # 80%-60%
    pygame.image.load("Assets/Animations/Logs/log_middle3.png").convert_alpha(),  # 60%-40%
    pygame.image.load("Assets/Animations/Logs/log_middle4.png").convert_alpha(),  # 40%-20%
    pygame.image.load("Assets/Animations/Logs/log_middle5.png").convert_alpha()   # 20%-0%
]
log_front_images = [
    pygame.image.load("Assets/Animations/Logs/log_front1.png").convert_alpha(),  # 100%-80%
    pygame.image.load("Assets/Animations/Logs/log_front2.png").convert_alpha(),  # 80%-60%
    pygame.image.load("Assets/Animations/Logs/log_front3.png").convert_alpha(),  # 60%-40%
    pygame.image.load("Assets/Animations/Logs/log_front4.png").convert_alpha(),  # 40%-20%
    pygame.image.load("Assets/Animations/Logs/log_front5.png").convert_alpha()   # 20%-0%
]

# Chroma key: make black (0, 0, 0) transparent
log_back_tile.set_colorkey((0, 0, 0))
log_middle_tile.set_colorkey((0, 0, 0))
log_front_tile.set_colorkey((0, 0, 0))
player_image.set_colorkey((0, 0, 0))
wood_tile.set_colorkey((0, 0, 0))
metal_tile.set_colorkey((0, 0, 0))
barrel_tile.set_colorkey((0, 0, 0))
add_tile.set_colorkey((0, 0, 0))
menu_image.set_colorkey((0, 0, 0))
water_splash_tile.set_colorkey((0, 0, 0))
auto_fisher_tile.set_colorkey((0, 0, 0))
repairer_tile.set_colorkey((0, 0, 0))

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
        screen.blit(resource_text, (self.x - TILE_SIZE/2, self.y + TILE_SIZE))
    
    def add_stock(self, amount):
        self.current_stock = min(self.current_stock + amount, self.max_stock)

    def set_stock(self, amount):
        self.current_stock = amount

    def remove_stock(self, amount):
        self.current_stock = max(self.current_stock - amount, 0)


# Log class to handle each log object
class Log:
    def __init__(self, x, y, level):
        self.x = x
        self.y = y
        self.level = level
        self.max_health = LOG_HEALTH * self.level
        self.health = self.max_health
        self.has_empty_spot = True
        self.log_back_images  = log_back_images
        self.log_middle_images = log_middle_images
        self.log_front_images = log_front_images
        self.destroyed_time = 0

    def get_log_back_image(self, part):
        # Calculate the health percentage
        health_percentage = self.health / self.max_health

        # Determine which image to use based on the health percentage
        if part == "back":
            if health_percentage >= 0.8:
                return self.log_back_images[0]
            elif health_percentage >= 0.6:
                return self.log_back_images[1]  # 80%-60%
            elif health_percentage >= 0.4:
                return self.log_back_images[2]  # 60%-40%
            elif health_percentage >= 0.2:
                return self.log_back_images[3]  # 40%-20%
            else:
                return self.log_back_images[4]  # 20%-0%
        elif part == "middle":
            if health_percentage >= 0.8:
                return self.log_middle_images[0]
            elif health_percentage >= 0.6:
                return self.log_middle_images[1]  # 80%-60%
            elif health_percentage >= 0.4:
                return self.log_middle_images[2]  # 60%-40%
            elif health_percentage >= 0.2:
                return self.log_middle_images[3]  # 40%-20%
            else:
                return self.log_middle_images[4]  # 20%-0%
        elif part == "front":
            if health_percentage >= 0.8:
                return self.log_front_images[0]
            elif health_percentage >= 0.6:
                return self.log_front_images[1]  # 80%-60%
            elif health_percentage >= 0.4:
                return self.log_front_images[2]  # 60%-40%
            elif health_percentage >= 0.2:
                return self.log_front_images[3]  # 40%-20%
            else:
                return self.log_front_images[4]  # 20%-0%

    def draw(self, player=None):
        # Determine the correct log_back image
        log_back_image = self.get_log_back_image("back")
        log_middle_image = self.get_log_back_image("middle")
        log_front_image = self.get_log_back_image("front")

        # Place log_back.png at the top
        screen.blit(log_back_image, (self.x, self.y - TILE_SIZE))
        # Place log_middle.png in the middle
        screen.blit(log_middle_image, (self.x, self.y))
        # Place log_front.png at the bottom
        screen.blit(log_front_image, (self.x, self.y + TILE_SIZE))
        #water_splash_tile
        screen.blit(water_splash_tile, (self.x, self.y + TILE_SIZE))

        # Draw the health bar above the log
        # font = pygame.font.SysFont(None, 24)
        # health_text = font.render(str(self.health), True, (255, 255, 255))
        # screen.blit(health_text, (self.x, self.y - TILE_SIZE * 2))

        # Only draw the add_tile if this is the log the player is on and it has an empty spot
        if player:
            if self.has_empty_spot and self.x == player.x and self.y == player.y:
                screen.blit(add_tile, (self.x, self.y - TILE_SIZE))

    def update(self, logs):
        damage = (sea_level + knots_speed) / 10  # Adjust the divisor to control how fast the logs break

        # Check if there are logs on both sides
        has_left_log = any(log.x == self.x - TILE_SIZE and log.y == self.y for log in logs)
        has_right_log = any(log.x == self.x + TILE_SIZE and log.y == self.y for log in logs)
    
        if player is None and not(has_left_log and has_right_log):
            # Add a delay before destroying the log
            if time.time() - self.destroyed_time >= 0.5:  # 0.5 seconds delay between each log
                self.health -= 9999999
                self.destroyed_time = time.time()  # Update the destroyed_time
        else:
            # Only decrease health if there isn't a log on both sides
            if not(has_left_log and has_right_log):
                self.health -= damage

        # Ensure health doesn't go below 0
        if self.health < 0:
            self.health = 0

    def restore_health(self, amount):
        self.health += amount

    def is_destroyed(self):
        # Check if the log is destroyed (health reaches 0)
        return self.health == 0
    
def draw_add_tile():
    for log in logs:
        if player and wood.current_stock >= 10:  # Only show the add_tile if there are enough resources and player exists
            if log.x == player.x and log.y == player.y:  # Check if the player is on this log
                can_build_left = not any(l.x == log.x - TILE_SIZE for l in logs)
                can_build_right = not any(l.x == log.x + TILE_SIZE for l in logs)

                # Show add_tile on the left if possible
                if can_build_left:
                    screen.blit(add_tile, (log.x - TILE_SIZE, log.y))

                # Show add_tile on the right if possible
                if can_build_right:
                    screen.blit(add_tile, (log.x + TILE_SIZE, log.y))

def handle_add_tile_click(mouse_x, mouse_y):
    for log in logs:
        if player and log.x == player.x and log.y == player.y:  # Ensure player is on this log
            can_build_left = not any(l.x == log.x - TILE_SIZE for l in logs)
            can_build_right = not any(l.x == log.x + TILE_SIZE for l in logs)

            if can_build_left and log.x - TILE_SIZE <= mouse_x <= log.x and log.y <= mouse_y <= log.y + TILE_SIZE:
                place_log(log.x - TILE_SIZE, log.y)

            if can_build_right and log.x + TILE_SIZE <= mouse_x <= log.x + 2 * TILE_SIZE and log.y <= mouse_y <= log.y + TILE_SIZE:
                place_log(log.x + TILE_SIZE, log.y)

def place_log(x, y):
    if wood.current_stock >= 10:  # Check if there are enough resources
        wood.remove_stock(10)
        logs.append(Log(x, y, 1))
    
class Bobber:
    def __init__(self, x, y):
        self.start_x = x
        self.start_y = y
        self.x = x
        self.y = y
        self.target_y = y + TILE_SIZE * 2  # 2 tiles below the player
        self.state = "rising"  # Initial state
        self.speed = 40  # Speed for movement
        self.animation_timer = 0
        self.dunking = False
        self.caught_fish = None  # Store the type of fish caught
        self.fish_image = None  # Store the image of the fish caught
        self.drift_direction = 0  # Amount of drift to the left or right
        self.fish_on_line_playing = False
        self.fish_sound_duration = fish_on_line_sound.get_length()
        self.fish_sound_start_time = 0

        # Load bobber animation frames
        self.bobber_frames = [
            pygame.image.load(f"Assets/bobber_dunk{i}.png").convert_alpha()
            for i in range(3, 7)  # Frames 3 to 6 for looping dunk animation
        ]
        self.current_frame = 0
        self.frame_count = len(self.bobber_frames)

        # Set a random delay between 1-5 seconds before dunking starts
        self.dunk_delay = random.uniform(1, 5)
        self.dunk_start_time = time.time()

        # Load fish images
        self.wood_fish_image = pygame.image.load("Assets/woodfish.png").convert_alpha()
        self.iron_fish_image = pygame.image.load("Assets/ironfish.png").convert_alpha()

    def update(self):
        if self.state == "rising":
            self.y -= self.speed  # Move up 3 tiles
            if self.y <= self.start_y - TILE_SIZE * 3:
                self.state = "falling"
        elif self.state == "falling":
            self.y += self.speed  # Move down to 2 tiles below the player
            if self.y >= self.target_y:
                self.state = "waiting"
        elif self.state == "waiting":
            if time.time() - self.dunk_start_time >= self.dunk_delay:
                self.state = "dunking"
                self.play_fish_on_line_sound()
            else:
                self.drift()  # Apply drift while waiting
        elif self.state == "dunking":
            self.animate_dunk()
        elif self.state == "raising":
            self.raise_bobber()
            if self.fish_on_line_playing:
                self.stop_fish_on_line_sound()

    def play_fish_on_line_sound(self):
        fish_on_line_sound.play()

    def stop_fish_on_line_sound(self):
        fish_on_line_sound.stop()
        self.fish_on_line_playing = False

    def drift(self):
        # Increase the drift effect
        desired_drift = -knots_speed * 0.3  # Drift left with increasing speed
        if self.drift_direction < desired_drift:
            self.drift_direction += 0.2  # Gradually drift left
        elif self.drift_direction > desired_drift:
            self.drift_direction -= 0.2  # Gradually drift right

        # Update the bobber's x position based on the drift
        self.x += self.drift_direction

    def animate_dunk(self):
        # Update animation frame based on timer
        self.animation_timer += 1
        if self.animation_timer % 1 == 0:  # Change frame every tick
            self.current_frame = (self.current_frame + 1) % self.frame_count

    def raise_bobber(self):
        self.y -= self.speed  # Raise the bobber
        if self.y <= self.start_y - TILE_SIZE * 3:
            self.state = "finished"
            # Add the corresponding resource to the player's inventory
            if self.caught_fish == "wood":
                wood.add_stock(5 + (sea_level*2))
            elif self.caught_fish == "metal":
                metal.add_stock(5 + (sea_level*2))
            player.complete_fishing()

    def select_fish(self):
        # 50/50 chance to catch either the woodfish or ironfish
        if random.choice([True, False]):
            self.caught_fish = "wood"
            self.fish_image = self.wood_fish_image
        else:
            self.caught_fish = "metal"
            self.fish_image = self.iron_fish_image

    def draw(self):
        if self.state in ["dunking", "raising"]:
            frame_image = self.bobber_frames[self.current_frame]
        else:
            frame_image = pygame.image.load("Assets/bobber_dunk6.png").convert_alpha()  # Default bobber image
        screen.blit(frame_image, (self.x, self.y))

        # Draw the fish if it has been caught
        if self.state == "raising" and self.caught_fish:
            screen.blit(self.fish_image, (self.x, self.y + 16))

    def on_click(self):
        # Handle when the player clicks on the bobber
        if self.state == "dunking":
            self.state = "raising"
            self.current_frame = 0
            self.select_fish()

# Player class to handle the player object
class Player:
    def __init__(self, x, y):
        self.image = player_image
        self.x = x
        self.y = y
        self.target_x = None
        self.start_x = None
        self.progress = 0
        self.speed = 0.8  # Speed attribute for sliding
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

        # Cancel the current slide and snap to the target log
        if self.target_x is not None:
            # Snap the player to the current target position before moving again
            self.x = self.target_x
            self.target_x = None

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
            self.target_x = new_x  # Set the new target x position
            self.progress = 0
        else:
            self.current_frame = 0


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

        # Update the bobber if it exists
        if self.bobber and self.bobber.state != "finished":
            self.bobber.update()

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
        self.progress += 0.4 # Increase progress based on speed

        # Apply easing (quadratic easing)
        easing_progress = self.ease_in_out(self.progress)

        # Interpolate the x position
        self.x = self.start_x + (self.target_x - self.start_x) * easing_progress

        # Update the current animation frame
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

    def complete_fishing(self):
        # Add resources after completing the fishing animation
        # wood.add_stock(5)  # Add 5 wood to the current stock
        self.is_fishing = False  # Stop fishing after resources are added
        self.bobber = None  # Remove the bobber after fishing is complete
        self.current_frame = 0

    def start_fishing(self):
        # Start the fishing animation
        self.is_fishing = True
        self.current_frame = 0
        cast_line_sound.play()
        self.bobber = Bobber(self.x, self.y)  # Start bobber at the player's position

    def handle_mouse_click(self, mouse_x, mouse_y):
        if self.bobber and self.bobber.state == "dunking":
            bobber_rect = pygame.Rect(self.bobber.x, self.bobber.y, TILE_SIZE, TILE_SIZE)
            if bobber_rect.collidepoint(mouse_x, mouse_y):
                self.bobber.on_click()

    def ease_in_out(self, t):
        return 3 * t**2 - 2 * t**3  # Smooth start and end

    def draw(self):
        if self.is_fishing:
            frame_image = self.fishing_frames[self.current_frame]
        else:
            frame_image = self.sliding_frames[self.current_frame]
        screen.blit(frame_image, (self.x, self.y - TILE_SIZE))
        # Draw the line if the bobber exists
        if self.bobber:
            # Calculate the line start and end positions
            line_start_x = self.x + TILE_SIZE // 2  # Center of the player's tile
            line_start_y = self.y - TILE_SIZE  # Top of the tile above the player
            line_end_x = self.bobber.x + TILE_SIZE // 2  # Adjusted for drift
            line_end_y = self.bobber.y + TILE_SIZE // 2  # Center of the bobber

            # Draw the line
            pygame.draw.line(screen, (0, 0, 0), (line_start_x, line_start_y), (line_end_x, line_end_y), 2)  # 2 is the line thickness
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

class Sail:
    def __init__(self, x, y, log):
        self.x = x
        self.y = y
        self.log = log
        self.frame = 0  # Current frame of the animation
        self.animation_speed = 5  # Control the speed of the animation (adjust as needed)
        self.animation_counter = 0  # Counts the frames for timing the animation

        # Load the sail animation frames
        self.sail_frames = [
            pygame.image.load(f"Assets/Animations/Sail/sail_animated{i}.png").convert_alpha()
            for i in range(1, 9)
        ]
        self.sprite = self.sail_frames[0]

        # Boolean to check if animation is done
        self.animation_done = False

    def update(self):
        if not self.animation_done:
            self.animation_counter += 1
            if self.animation_counter >= self.animation_speed:
                self.frame += 1
                if self.frame < len(self.sail_frames):
                    self.sprite = self.sail_frames[self.frame]
                else:
                    self.sprite = self.sail_frames[-1]  # Stay on the last frame
                    self.animation_done = True
                self.animation_counter = 0

    def draw(self):
        screen.blit(self.sprite, (self.x, self.y))

class AutoFisher:
    def __init__(self, x, y, log, sprite):
        self.x = x
        self.y = y
        self.log = log
        self.sprite = sprite
        self.resource_type = None
        self.caught_fish = None
        self.catch_timer = 0
        self.catch_interval = random.randint(5, 6)  # Catch a fish every 5-6 seconds
        self.wood_fish_image = pygame.image.load("Assets/woodfish.png").convert_alpha()
        self.iron_fish_image = pygame.image.load("Assets/ironfish.png").convert_alpha()

    def select_resource(self, resource_type):
        self.resource_type = resource_type

    def update(self):
        # Only start catching fish if a resource type is selected
        if self.resource_type and knots_speed != 0:
            self.catch_timer += 1
            if self.catch_timer >= self.catch_interval * 10:  # Multiply by 10 for a reasonable in-game time
                if self.caught_fish is None:
                    self.caught_fish = self.resource_type
                    self.catch_timer = 0

    def draw(self):
        screen.blit(self.sprite, (self.x, self.y))
        if self.caught_fish == "wood":
            screen.blit(self.wood_fish_image, (self.x, self.y))
        elif self.caught_fish == "metal":
            screen.blit(self.iron_fish_image, (self.x, self.y))

    def on_click(self):
        resource_amount = 1 + sea_level  # Increase the resource amount based on the sea level
        if self.caught_fish == "wood":
            wood.add_stock(resource_amount)
        elif self.caught_fish == "metal":
            metal.add_stock(resource_amount)
        self.caught_fish = None

class Repairer:
    def __init__(self, x, y, log, sprite):
        self.x = x
        self.y = y + TILE_SIZE
        self.log = log
        self.sprite = sprite
        self.repair_sprites = [
            pygame.image.load("Assets/Animations/Repairer/repairer1.png").convert_alpha(),
            pygame.image.load("Assets/Animations/Repairer/repairer2.png").convert_alpha(),
            pygame.image.load("Assets/Animations/Repairer/repairer3.png").convert_alpha(),
            pygame.image.load("Assets/Animations/Repairer/repairer4.png").convert_alpha()
        ]
        self.current_frame = 0
        self.frame_count = len(self.repair_sprites)
        self.animation_speed = 1  # Adjust for speed of animation
        self.animation_timer = 0
        self.repairing = False
        self.waiting_for_next_repair = False  # New attribute to handle waiting between repairs

    def update(self):
        if self.log.health < self.log.max_health and metal.current_stock >= 5:
            self.repairing = True
            self.waiting_for_next_repair = False
        else:
            self.repairing = False
            self.waiting_for_next_repair = False
            self.current_frame = 0  # Reset to the first frame when not repairing

    def animate_repair(self):
        if self.repairing:
            self.animation_timer += 1
            if self.animation_timer >= self.animation_speed:
                self.animation_timer = 0
                self.current_frame = (self.current_frame + 1) % self.frame_count

                # When the last frame is reached, perform the repair action
                if self.current_frame == self.frame_count - 1:
                    metal.remove_stock(5)
                    self.log.restore_health(10)

                    # Check if the log is fully repaired or no more metal is available
                    if self.log.health >= self.log.max_health or metal.current_stock < 5:
                        self.repairing = False
                        self.current_frame = 0

    def draw(self):
        # Draw the current frame of the repair animation if repairing, otherwise draw the idle sprite
        screen.blit(self.repair_sprites[self.current_frame], (self.x, self.y))



def show_build_selection_menu():
    # Draw the menu background
    menu_width, menu_height = 200, 200  # Increased height to accommodate the fourth option
    menu_x = SCREEN_WIDTH // 2 - menu_width // 2
    menu_y = SCREEN_HEIGHT // 2 - menu_height // 2
    pygame.draw.rect(screen, (0, 0, 0), (menu_x, menu_y, menu_width, menu_height))

    # Draw the options
    font = pygame.font.SysFont(None, 24)
    barrel_option = font.render("Build Barrel", True, (255, 255, 255))
    sail_option = font.render("Build Sail", True, (255, 255, 255))
    auto_fisher_option = font.render("Build Auto Fisher", True, (255, 255, 255))
    repairer_option = font.render("Build Repairer", True, (255, 255, 255))

    screen.blit(barrel_option, (menu_x + 20, menu_y + 20))
    screen.blit(sail_option, (menu_x + 20, menu_y + 60))
    screen.blit(auto_fisher_option, (menu_x + 20, menu_y + 100))
    screen.blit(repairer_option, (menu_x + 20, menu_y + 140))

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
                        return "barrel"
                    elif menu_y + 40 < mouse_y < menu_y + 80:
                        return "sail"
                    elif menu_y + 80 < mouse_y < menu_y + 120:
                        return "auto_fisher"
                    elif menu_y + 120 < mouse_y < menu_y + 160:
                        return "repairer"

def place_structure_on_log(log):
    global knots_speed
    # Show build selection menu
    build_choice = show_build_selection_menu()
    
    if build_choice == "barrel":
        # Show the resource selection menu if Barrel is selected
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

    elif build_choice == "sail":
        # Place a sail on the log
        sails.append(Sail(log.x, log.y - TILE_SIZE *2, log))
        log.has_empty_spot = False  # Mark the spot as used
        knots_speed += 1  # Increase knots speed
        # (You can add a sound effect for placing the sail here if desired)

    elif build_choice == "auto_fisher":
        selected_resource = show_resource_selection_menu()
        auto_fisher = AutoFisher(log.x, log.y - TILE_SIZE, log, auto_fisher_tile)
        auto_fisher.select_resource(selected_resource)
        auto_fishers.append(auto_fisher)
        log.has_empty_spot = False

    elif build_choice == "repairer":
        repairers.append(Repairer(log.x, log.y - TILE_SIZE * 2, log, repairer_tile))
        log.has_empty_spot = False

def show_resource_selection_menu():
    # Draw the menu background
    menu_width, menu_height = 200, 150
    menu_x = SCREEN_WIDTH // 2 - menu_width // 2
    menu_y = SCREEN_HEIGHT // 2 - menu_height // 2
    pygame.draw.rect(screen, (0, 0, 0), (menu_x, menu_y, menu_width, menu_height))

    # Draw the options
    font = pygame.font.SysFont(None, 24)
    wood_option = font.render("Wood", True, (255, 255, 255))
    metal_option = font.render("Metal", True, (255, 255, 255))
    
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
                    
def draw_menu_with_distance():
    # Render the distance text
    distance_number = str(int(distance_travelled))  # Convert the integer part to string
    distance_text = menu_font.render(distance_number, True, (255, 255, 255))  # White text
    distance_text_rect = distance_text.get_rect(center=(menu_x + 230, menu_y + 80))
    # Render the high score text
    hiscore_text = menu_font.render(f"{hiscore}", True, (255, 255, 255))
    hiscore_text_rect = hiscore_text.get_rect(center=(menu_x + 230, menu_y + 145))

    # Draw the menu image
    screen.blit(menu_image, (menu_x, menu_y))
    # Draw the distance text on top of the menu
    screen.blit(distance_text, distance_text_rect)
    screen.blit(hiscore_text, hiscore_text_rect)

def draw_overlay(screen, sea_level):
    """Draw a dark blue overlay that increases in opacity with the sea level."""
    # Calculate the alpha value based on sea level
    max_sea_level = 10  # Adjust as needed
    alpha = min(int(255 * (0.1 * sea_level / max_sea_level)), 25)  # Max 10% opacity (25/255)
    
    # Create a surface with the same size as the screen
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(alpha)  # Set the alpha transparency level
    overlay.fill((0, 0, 50))  # Fill with a dark blue color (RGB: 0, 0, 139)
    
    # Blit the overlay on the screen
    screen.blit(overlay, (0, 0))

def create_background_surface(background_frames, screen_width, screen_height):
    """Combine background tiles into a single surface."""
    background_surface = pygame.Surface((screen_width, screen_height))
    tile_width, tile_height = background_frames[0].get_size()
    rows = screen_height // tile_height + 1
    cols = screen_width // tile_width + 1

    for row in range(rows):
        for col in range(cols):
            tile_x = col * tile_width
            tile_y = row * tile_height
            background_surface.blit(background_frames[0], (tile_x, tile_y))  # Start with the first frame

    return background_surface

def scroll_background(screen, background_surface, background_offset, scroll_speed):
    """Scroll the background surface."""
    background_width = background_surface.get_width()
    # Move the background
    background_offset -= scroll_speed

    # If the background has scrolled off the screen, reset it
    if background_offset <= -background_width:
        background_offset = 0

    # Draw the background twice to create a continuous scroll effect
    screen.blit(background_surface, (background_offset, 0))
    screen.blit(background_surface, (background_offset + background_width, 0))

    return background_offset

def load_hiscore():
    try:
        with open("hiscore.txt", "r") as file:
            return int(file.read())
    except FileNotFoundError:
        return 0  # If the file doesn't exist, start with a score of 0

hiscore = load_hiscore()
game_over_sound_played = False

def save_hiscore(score):
    with open("hiscore.txt", "w") as file:
        file.write(str(score))
                    
def restart_game():
    global player, logs, barrels, sails, knots_speed, distance_travelled, distance_meter, menu_falling, menu_landed, menu_y, sea_level, repairers, auto_fishers

    # Reset the game state
    logs = []
    barrels = []
    sails = []
    repairers = []
    auto_fishers = []
    knots_speed = 0
    distance_travelled = 0
    distance_meter = 0
    sea_level = 0
    menu_falling = False
    menu_landed = False
    menu_y = -320  # Reset menu position
    wood.set_stock(STARTING_RESOURCES)
    metal.set_stock(STARTING_RESOURCES)

    # Create and add 3 logs spaced horizontally
    logs.append(Log(center_x := (COLS // 2) * TILE_SIZE, center_y := (ROWS // 2) * TILE_SIZE, 4))
    logs.append(Log(center_x + TILE_SIZE, center_y, 2))
    logs.append(Log(center_x - TILE_SIZE, center_y, 2))

    # Create the player and place it on the first log
    player = Player(center_x, center_y - TILE_SIZE)

# Main game loop
running = True
logs = []
barrels = []
sails = []
auto_fishers = []
repairers = []
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

# Initialize the background surface
    background_surface = create_background_surface(background_frames, SCREEN_WIDTH, SCREEN_HEIGHT)
    background_offset = 0  # This will track the scroll position

# Update the background speed
background_speed = knots_speed
background_moving = True  # Track if the background is moving

# Create resources
wood = Resource("wood", SCREEN_WIDTH // 2 - TILE_SIZE - TILE_SIZE, TILE_SIZE, STARTING_RESOURCES, 100, wood_tile)
metal = Resource("metal", SCREEN_WIDTH // 2 + TILE_SIZE + TILE_SIZE, TILE_SIZE, STARTING_RESOURCES, 100, metal_tile)

# Create and add 3 logs spaced horizontally
logs.append(Log(center_x := (COLS // 2) * TILE_SIZE, center_y := (ROWS // 2) * TILE_SIZE, 3))
logs.append(Log(center_x + TILE_SIZE, center_y, 2))
logs.append(Log(center_x - TILE_SIZE, center_y, 2))

# Create the player and place it on the first log
player = Player(center_x, center_y - TILE_SIZE)

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
                running = False
        if player:            
            if event.type == pygame.KEYDOWN:
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
                elif event.key == pygame.K_o:  # Increase knots speed
                    knots_speed += 1
                elif event.key == pygame.K_p:  # Decrease knots speed
                    knots_speed = max(0, knots_speed - 1)  # Ensure it doesn't go below 0
            # Separate MOUSEBUTTONDOWN handling
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos
                handle_add_tile_click(mouse_x, mouse_y)
                player.handle_mouse_click(mouse_x, mouse_y)
                for log in logs:
                    # Check if the click is on the add_tile and the log has an empty spot
                    if log.has_empty_spot and log.x <= mouse_x <= log.x + TILE_SIZE and log.y - TILE_SIZE <= mouse_y <= log.y:
                        if log.x == player.x and log.y == player.y:  # Ensure the player is on the log
                            place_structure_on_log(log)
                            break
                for auto_fisher in auto_fishers:
                    if auto_fisher.x <= mouse_x <= auto_fisher.x + TILE_SIZE and auto_fisher.y <= mouse_y <= auto_fisher.y + TILE_SIZE:
                        auto_fisher.on_click()
        else:
            # New event handling when the player does not exist
            if event.type == pygame.MOUSEBUTTONDOWN and menu_landed:
                # Restart the game when the menu is clicked
                game_over_sound_played = False
                # Stop the menu music and restart the background music
                pygame.mixer.music.stop()  # Stop the menu music
                pygame.mixer.music.load("Assets/Sounds/background_music.wav")  # Load the background music
                pygame.mixer.music.play(-1)  # Play the background music on loop
                restart_game()
    
    if not player:
        menu_falling = True

    if menu_falling and not menu_landed:
        menu_y += menu_fall_speed
        if menu_y >= SCREEN_HEIGHT // 2 - 160:  # Center the menu vertically
            menu_y = SCREEN_HEIGHT // 2 - 160
            menu_landed = True
    
    distance_meter += knots_speed

    # Check if distance_meter has reached or exceeded the threshold for 1 meter
    if distance_meter >= METER_DISTANCE_PER_KNOT:
        meters_to_add = distance_meter // METER_DISTANCE_PER_KNOT  # Calculate full meters to add
        distance_travelled += meters_to_add
        distance_meter %= METER_DISTANCE_PER_KNOT  # Carry over the remainder
        # Update sea level every 50 meters
        if distance_travelled // 50 > sea_level:
            sea_level = distance_travelled // 50


    # Update the background speed
    background_speed = knots_speed

    # In the main game loop:
    background_offset = scroll_background(screen, background_surface, background_offset, background_speed)

    draw_overlay(screen, sea_level)

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
            # Remove any sails on this log and decrease the knots speed
            for sail in sails[:]:
                if sail.log == log:
                    sails.remove(sail)
                    knots_speed -= 1  # Decrease knots speed when the sail is removed
            for auto_fisher in auto_fishers[:]:
                if auto_fisher.log == log:
                    auto_fishers.remove(auto_fisher)
            for repairer in repairers[:]:
                if repairer.log == log:
                    repairers.remove(repairer)

    # Ensure the add_tile is drawn in the main game loop
    draw_add_tile()

    # Draw all barrels
    for barrel in barrels:
        barrel.draw()

    # Draw all sails
    for sail in sails:
        sail.update()
        sail.draw()

    # Update and draw all AutoFishers
    for auto_fisher in auto_fishers:
        auto_fisher.update()
        auto_fisher.draw()

    for repairer in repairers:
        repairer.update()
        repairer.animate_repair()
        repairer.draw()

    # Update and draw the player
    if player:
        player.draw()
        if player.update(logs):
            player = None  # Delete the player if they fall off the log        

    # Drawing the distance travelled at the top right corner
    font = pygame.font.SysFont(None, 24)
    distance_text = font.render(f"Distance: {distance_travelled} m", True, (255, 255, 255))
    screen.blit(distance_text, (SCREEN_WIDTH - 150, 10))
    # Drawing the knots speed just below the distance text
    knots_speed_text = font.render(f"Speed: {knots_speed} knots", True, (255, 255, 255))
    screen.blit(knots_speed_text, (SCREEN_WIDTH - 150, 40))
    # Drawing the sea level just below the knots speed text
    sea_level_text = font.render(f"Sea Level: {sea_level}", True, (255, 255, 255))
    screen.blit(sea_level_text, (SCREEN_WIDTH - 150, 70))  # Positioned 30 pixels below the knots_speed_text


    if player == None:
        if distance_travelled > hiscore:
            hiscore = distance_travelled
            save_hiscore(hiscore)    
        draw_menu_with_distance()
        
        if not game_over_sound_played:
            game_over_sound.play()  # Play the game-over sound
            game_over_sound_played = True  # Set the flag to True to prevent replaying
            # Stop the background music and play the menu music
            pygame.mixer.music.stop()  # Stop the background music
            pygame.mixer.music.load("Assets/Sounds/menu_music.wav")  # Load the menu music
            pygame.mixer.music.play(-1)  # Play the menu music on loop

    # Update the display
    pygame.display.flip()

    # Control the frame rate
    pygame.time.delay(100)  # Delay to slow down health decrease

# Quit Pygame
pygame.quit()
sys.exit()