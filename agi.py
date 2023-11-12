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

def make_slides(pdf):
    pdf_file = "output/paper.pdf"
    open(pdf_file, 'wb').write(pdf)

    extract.extract_text(pdf_file, 'output')
    extract.process_files_in_order('attention', 'output')
    messages, md = gen_md.generate_md(pdf_file)
    return messages, md

def normalise_slides(md):
    md = md.strip().strip('-').strip()
    return md

def get_slide_texts(voiceover):
    # shitty heuristic: lines with over 50 chars are voiceover lines.
    voiceover = voiceover.split('\n')
    return [line for line in voiceover if len(line) > 50]

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

def get_tts(voiceover):
    texts = get_slide_texts(voiceover)
    threads = []
    for i, text in enumerate(texts):
        # Run in a separate thread 
        thread = threading.Thread(target=generate_tts_slide, args=(text, i))
        thread.start()
        threads.append(thread)

    # join all threads
    for thread in threads:
        thread.join()

    return len(texts)

client = OpenAI()

# with Halo(text='Generating beautiful slides...', spinner='dots'):
spinner = Halo(text='Generating beautiful slides...', spinner='dots')
spinner.start()
messages, slides = make_slides(pdf)
slides = normalise_slides(slides)
spinner.stop_and_persist(symbol='✅')

# TODO: Generate voiceover text
spinner = Halo(text='Generating voiceover text...', spinner='dots')
messages += [
    {"role": "assistant", "content": slides},
    {"role": "user", "content": "Generate a transcript of some engaging voiceover for the slides. For each slide, write about 20 seconds of useful speech as if presenting this as a lightning talk at a conference. Take the text already on each slide for granted, complementing it with an explanation. Don't say 'Slide X', just separate the slides with newlines."},
]
completion = client.chat.completions.create(
    model="gpt-4-1106-preview",
    messages=messages,
    max_tokens=4096
)

voiceover = completion.choices[0].message.content
print(voiceover)
spinner.stop_and_persist(symbol='✅')

# with Halo(text='Generating slide layout...', spinner='dots'):
spinner = Halo(text='Generating slide layout...', spinner='dots')
spinner.start()
open('output/slides_normed.md', 'w').write(slides)
os.system("darkslide output/slides_normed.md -i")
spinner.stop_and_persist(symbol='✅')

spinner = Halo(text='Generating voiceover (in parallel)...', spinner='dots')
spinner.start()
n_slides = get_tts(voiceover)
spinner.stop_and_persist(symbol='✅')