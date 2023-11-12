from pathlib import Path
from openai import OpenAI
from halo import Halo
from darkslide import generator
import os
import threading
import re
import requests
client = OpenAI()
import gen_md
import extract

def fetch_paper(paper_id):
    # examples:
    # https://arxiv.org/abs/2206.07840
    # 2206.07840
    # https://arxiv.org/pdf/2206.07840.pdf
    pid = re.findall(r'\d{4}\.\d{5}', paper_id)[0]
    url = f'https://arxiv.org/pdf/{pid}.pdf'
    spinner = Halo(text=f'Fetching paper {pid}...', spinner='dots')
    spinner.start()
    resp = requests.get(url)
    spinner.stop_and_persist(symbol='✅')
    return resp.content

print('What paper did you forget to make slides for?')

paper_id = input()
pdf = fetch_paper(paper_id)

# DUMMY!
def make_slides(pdf):
    pdf_file = "output/paper.pdf"
    open(pdf_file, 'wb').write(pdf)
    extract.extract_figures_and_text(pdf_file, 'output')
    return gen_md.generate_md(pdf_file)


def normalise_slides(md):
    md = md.strip().strip('-').strip()
    return md

# DUMMY!
def get_slide_texts(slides):
    text = open('voiceover.md', 'r').read().splitlines()
    # shitty heuristic: lines with over 20 chars are voiceover lines.
    return [line for line in text if len(line) > 20]

def get_tts_resp(text):
    return client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text,
        speed=1.15, 
    )

def generate_tts_slide(text, i):
    resp = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text,
            speed=1.15, 
        )
    
    resp.stream_to_file(f"output/slide_{i}.mp3")
    print('out', i)

def get_tts(slides):
    texts = get_slide_texts(slides)
    threads = []
    for i, text in enumerate(texts):
        # Run in a separate thread 
        thread = threading.Thread(target=generate_tts_slide, args=(text, i))
        thread.start()
        threads.append(thread)

    # join all threads
    for thread in threads:
        thread.join()

client = OpenAI()

with Halo(text='Generating beautiful slides...', spinner='dots'):
    slides = make_slides(pdf)
    slides = normalise_slides(slides)

# TODO: Generate voiceover text

with Halo(text='Generating slide layout...', spinner='dots'):
    open('output/slides_normed.md', 'w').write(slides)
    os.system("darkslide output/slides_normed.md -i")

with Halo(text='Generating engaging voiceover...', spinner='dots'):
    get_tts(None)

