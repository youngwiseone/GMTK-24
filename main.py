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

# Set up the display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Build to Scale - Raft Game")

# Load images from the Assets folder
background_tile = pygame.image.load("Assets/sky.png").convert()
log_back_tile = pygame.image.load("Assets/log_back.png").convert()
log_middle_tile = pygame.image.load("Assets/log_middle.png").convert()
log_front_tile = pygame.image.load("Assets/log_front.png").convert()

# Chroma key: make black (0, 0, 0) transparent
log_back_tile.set_colorkey((0, 0, 0))
log_middle_tile.set_colorkey((0, 0, 0))
log_front_tile.set_colorkey((0, 0, 0))

# Function to place a log (all three parts)
def place_log(x, y):
    # Place log_back.png at the top
    screen.blit(log_back_tile, (x, y - TILE_SIZE))
    # Place log_middle.png in the middle
    screen.blit(log_middle_tile, (x, y))
    # Place log_front.png at the bottom
    screen.blit(log_front_tile, (x, y + TILE_SIZE))

# Main game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Fill the screen with the background tile (sky.png)
    for row in range(ROWS):
        for col in range(COLS):
            screen.blit(background_tile, (col * TILE_SIZE, row * TILE_SIZE))

    # Place a log at a specific location (center of the screen)
    center_x = (COLS // 2) * TILE_SIZE
    center_y = (ROWS // 2) * TILE_SIZE
    place_log(center_x, center_y)
    place_log(center_x + TILE_SIZE, center_y)

    # Update the display
    pygame.display.flip()

# Quit Pygame
pygame.quit()
sys.exit()