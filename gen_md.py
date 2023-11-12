from openai import OpenAI
import os

import glob


def list_image_files(directory):
    # Define the image file extensions
    extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp']

    # List to hold all image file names
    image_files = []

    # Loop through each extension and add the files to the list
    for ext in extensions:
        image_files.extend(glob.glob(os.path.join(directory, ext)))

    return image_files

def generate_md(pdf_file):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY") or "YOUR_KEY_HERE")

    promt = f"""
    You are a scientific paper to presentation creator. Read the pdf provided and generate the summary in 6 slides in markdown format.

    Specifically, use: --- to delimit a new slide
    # to delimit a slide title

    Standard subheadings and bullet points from markdown.
    To insert an image use markdown "![image info](PATH)". Example: ![image info](image2_3.png) to insert third image from page 2 on this slide.
    Following images are vailable: {list_image_files("output")}
    On the slides with images don't use a lot of text, but still have some, because images take a lot of space.

    Do not write anything else, such as "Slide 1". Make sure the first slide is a title slide, showing the name of the paper and authors.

    Following is the paper to be created Markdown presentation from:

    """

    def read_and_combine_files(prefix, start=1):
        combined_text = ""
        page_number = start

        while True:
            # Construct the filename
            filename = f"output/{prefix}_{page_number}.txt"

            # Check if the file exists
            if not os.path.exists(filename):
                break

            # Read the file and append its content
            with open(filename, 'r') as file:
                combined_text += f"PAGE NUMBER {page_number}\n"
                combined_text += file.read() + "\n"

            page_number += 1

        return combined_text

    # Usage
    combined_text = read_and_combine_files("text_page")

    messages = [
        {"role": "system", "content": promt},
        {"role": "user", "content": combined_text}
    ]

    completion = client.chat.completions.create(
    model="gpt-4-1106-preview",
    messages=messages,
    max_tokens=4096
    )

    # Print out the generated markdown for the slides
    return messages, completion.choices[0].message.content
