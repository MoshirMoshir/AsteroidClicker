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
    'Overcharge': cv2.imread('special_5.png', cv2.IMREAD_GRAYSCALE)
}
reference_images_np = {key: np.array(img) for key, img in asteroid_images.items()}

# Scale of asteroids for each zoom level (small and big)
scale_factors = [0.2, 0.25, 0.4, 0.5, 0.9]

# Initialize the mouse controller
mouse = Controller()

# Function to match the template at a specific scale for each image
def match_template(scale, screenshot, reference_image_np):
    resized_reference = cv2.resize(reference_image_np, (0, 0), fx=scale, fy=scale)
    result = cv2.matchTemplate(screenshot, resized_reference, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    return max_val, max_loc, scale

# Function to find and click asteroids
def find_and_click():
    logging.debug('Finding Asteroids...')
    try:
        # Take a screenshot of the screen, downscale, and convert to grayscale numpy array
        screenshot = pyautogui.screenshot()
        screenshot_np = np.array(screenshot)
        downscale_factor = 0.5
        screenshot_np_small = cv2.resize(screenshot_np, (0, 0), fx=downscale_factor, fy=downscale_factor)
        screenshot_gray = cv2.cvtColor(screenshot_np_small, cv2.COLOR_RGB2GRAY)

        best_val = -1
        best_loc = None
        best_scale = None
        best_type = None

        # Iterate over each reference image and scales
        for asteroid_type, reference_image_np in reference_images_np.items():
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
            reference_height, reference_width = reference_images_np[best_type].shape[:2]
            center_x = int((start_x + reference_width * best_scale / 2) / downscale_factor)
            center_y = int((start_y + reference_height * best_scale / 2) / downscale_factor)

            # Mouse interface
            for i in range(5):
                logging.debug(f'Clicking on {best_type} asteroid at ({center_x}, {center_y})')
                mouse.position = (center_x, center_y)
                mouse.click(Button.left, 1)
                logging.debug(f'Clicked {i + 1} times.')

                if keyboard.is_pressed('q'):
                    logging.warning('Stopping program as "q" was pressed.')
                    return False

            logging.info(f'Destroyed {best_type} asteroid')
            return True
        else:
            logging.warning("Asteroid not found")
            return True
    except Exception as e:
        logging.error(f"Error occurred: {e}")
        return True

# Main loop
try:
    logging.info('Starting program. Press "q" to stop.')
    while True:
        if not find_and_click():
            break
        if keyboard.is_pressed('q'):
            logging.warning('Stopping program as "q" was pressed.')
            break
except KeyboardInterrupt:
    logging.info('Program stopped by user.')
