# Open html file in browser (macOS)
import pyautogui

import subprocess
import time
import os

def run_presentation(n_slides):
    os.system("open presentation.html")
    time.sleep(2)
    for i in range(n_slides):
        path = f"output/slide_{i}.mp3"
        subprocess.run(["afplay", path]) 
        pyautogui.press('space')

if __name__ == '__main__':
    run_presentation(7)