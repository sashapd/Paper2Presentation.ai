import fitz  # PyMuPDF
from extract_figures_tables import process_files_in_order

def extract_images_from_page(doc, page, output_dir):
    """Extracts images from a given page."""
    image_list = page.get_images(full=True)
    image_info = []
    for img_index, img in enumerate(image_list, start=1):
        xref = img[0]
        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]
        image_ext = base_image["ext"]
        image_filename = f"{output_dir}/image{page.number + 1}_{img_index}.{image_ext}"
        with open(image_filename, "wb") as image_file:
            image_file.write(image_bytes)
        image_info.append(image_filename)
    return image_info

def extract_text_from_page(page):
    """Extracts text (potentially including table data) from a given page."""
    text = page.get_text("text")
    return text

def extract_text(pdf_path, output_dir):
    doc = fitz.open(pdf_path)
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        
        # Extract images
        # images = extract_images_from_page(doc, page, output_dir)
        # print(f"Extracted images from page {page_num + 1}: {images}")

        # Extract text
        text = extract_text_from_page(page)
        with open(f"{output_dir}/text_page_{page_num + 1}.txt", "w") as text_file:
            text_file.write(text)
        print(f"Extracted text from page {page_num + 1}")

    doc.close()

if __name__ == '__main__':
    extract_text('1706.03762.pdf', 'output')
    process_files_in_order('mistral', 'output')
    

