import pyautogui
import cv2
import numpy as np
import logging
import keyboard
from concurrent.futures import ThreadPoolExecutor
from pynput.mouse import Controller, Button
import sys

# Check for debug mode
debug_mode = 'debug' in sys.argv
logging.basicConfig(level=logging.DEBUG if debug_mode else logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')

# Load the reference images and convert them to grayscale numpy arrays
asteroid_images = {
    'Normal': cv2.imread('asteroid.png', cv2.IMREAD_GRAYSCALE),
    'Cache': cv2.imread('special_1.png', cv2.IMREAD_GRAYSCALE),
    'Candy': cv2.imread('special_2.png', cv2.IMREAD_GRAYSCALE),
    'Upgrade': cv2.imread('special_3.png', cv2.IMREAD_GRAYSCALE),
    'Fuel': cv2.imread('special_4.png', cv2.IMREAD_GRAYSCALE),
    'Overcharge': cv2.imread('special_5.png', cv2.IMREAD_GRAYSCALE),
    'Multiplier': cv2.imread('special_6.png', cv2.IMREAD_GRAYSCALE)
}

secondary_images = {
    'Big_1': cv2.imread('big_1.png', cv2.IMREAD_GRAYSCALE),
    'Big_2': cv2.imread('big_2.png', cv2.IMREAD_GRAYSCALE),
    'Small_1': cv2.imread('small_1.png', cv2.IMREAD_GRAYSCALE),
    'Small_2': cv2.imread('small_2.png', cv2.IMREAD_GRAYSCALE)
}

reference_images_np = {key: np.array(img) for key, img in asteroid_images.items()}
secondary_images_np = {key: np.array(img) for key, img in secondary_images.items()}

# Scale of asteroids for each zoom level (small and big)
scale_factors = [0.2, 0.25, 0.4, 0.5, 0.9]

# Initialize the mouse controller
mouse = Controller()

# Function to match the template at a specific scale for each image
def match_template(scale, screenshot, reference_image_np):
    try:
        resized_reference = cv2.resize(reference_image_np, (0, 0), fx=scale, fy=scale)
        result = cv2.matchTemplate(screenshot, resized_reference, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        return max_val, max_loc, scale
    except Exception as e:
        logging.error(f"Error in match_template at scale {scale} with error: {e}")
        return -1, None, None

# Function to find and click asteroids based on a given set of images
def find_and_click_asteroids(images_dict):
    best_val = -1
    best_loc = None
    best_scale = None
    best_type = None

    # Take a screenshot of the screen, downscale, and convert to grayscale numpy array
    screenshot = pyautogui.screenshot()
    screenshot_np = np.array(screenshot)
    downscale_factor = 0.5
    screenshot_np_small = cv2.resize(screenshot_np, (0, 0), fx=downscale_factor, fy=downscale_factor)
    screenshot_gray = cv2.cvtColor(screenshot_np_small, cv2.COLOR_RGB2GRAY)

    for asteroid_type, reference_image_np in images_dict.items():
        with ThreadPoolExecutor() as executor:
            results = list(executor.map(lambda scale: match_template(scale, screenshot_gray, reference_image_np), scale_factors))

        # Check if we have a new best match
        for max_val, max_loc, scale in results:
            if max_val > best_val:
                best_val = max_val
                best_loc = max_loc
                best_scale = scale
                best_type = asteroid_type

    if best_val > 0.7:  # Confidence Value of match
        logging.debug(f'{best_type.capitalize()} asteroid found at scale {best_scale} with match value {best_val}')
        start_x, start_y = best_loc
        reference_height, reference_width = images_dict[best_type].shape[:2]
        center_x = int((start_x + reference_width * best_scale / 2) / downscale_factor)
        center_y = int((start_y + reference_height * best_scale / 2) / downscale_factor)

        # Click five times at the identified location
        logging.debug(f'Clicking on {best_type} asteroid at ({center_x}, {center_y})')
        mouse.position = (center_x, center_y)
        mouse.click(Button.left, 5)

        # Move the mouse out of the way
        screen_width, screen_height = pyautogui.size()
        mouse.position = (screen_width / 2, screen_height - 10)
        logging.debug('Mouse moved out of the way.')

        logging.info(f'Destroyed {best_type} asteroid')
        return True
    else:
        logging.warning("Asteroid not found")
        return False

# Main loop
try:
    logging.info('Starting program. Press "q" to stop.')
    while True:
        # First, try to find and click the primary asteroids
        primary_found = find_and_click_asteroids(reference_images_np)
        if not primary_found:
            # If no primary asteroids are found, try the secondary asteroids
            secondary_found = find_and_click_asteroids(secondary_images_np)
            if not secondary_found:
                logging.warning("No secondary asteroids found")

        if keyboard.is_pressed('q'):
            logging.warning('Stopping program as "q" was pressed.')
            break
except KeyboardInterrupt:
    logging.info('Program stopped by user.')
