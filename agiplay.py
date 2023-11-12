# Open html file in browser (macOS)
import pyautogui

import subprocess
import time
import os



def run_presentation(n_slides):

    from selenium import webdriver
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.by import By
    import time

    # Set up the WebDriver (This example uses Chrome; you can change it as needed)
    driver = webdriver.Chrome()
    driver.switch_to.window(driver.current_window_handle)

    # Open the file in the browser
    driver.get(f"file://{os.getcwd()}/presentation.html")
    # os.system("open presentation.html")
    time.sleep(1)
    for i in range(n_slides):
        path = f"output/slide_{i}.mp3"
        subprocess.run(["afplay", path]) 
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.SPACE)
        time.sleep(1)
        # pyautogui.press('space')

if __name__ == '__main__':
    run_presentation(7)