import os
import re
import shutil
import subprocess
from pylatexenc.latexwalker import (
    LatexWalker,
    LatexEnvironmentNode,
    LatexMacroNode,
)
from PIL import Image


def find_main_tex_file(directory):
    for filename in os.listdir(directory):
        if filename.endswith('.tex'):
            with open(os.path.join(directory, filename), 'r') as file:
                if '\\documentclass{' in file.read():
                    return filename
    return None


def extract_referenced_files(main_file_path):
    referenced_files = []
    with open(main_file_path, 'r') as file:
        for line in file:
            if '\\input{' in line or '\\include{' in line:
                # Extract the file reference from the line
                ref_file = line.split('{')[1].split('}')[0] + '.tex'
                referenced_files.append(ref_file)
    return referenced_files


def process_files_in_order(input_directory, output_directory):
    main_file = find_main_tex_file(input_directory)
    if main_file:
        main_file_path = os.path.join(input_directory, main_file)
        referenced_files = extract_referenced_files(main_file_path)
        referenced_files.append(main_file)
        table_count = 1
        figure_count = 1
        for ref_file in referenced_files:
            ref_file_path = os.path.join(input_directory, ref_file)
            # Now process each referenced file
            table_count, figure_count = process_tex_file(
                ref_file_path, output_directory, table_count, figure_count, input_directory
            )



def process_tex_files(input_directory, output_directory):
    table_count = 1
    figure_count = 1
    for filename in os.listdir(input_directory):
        if filename.endswith(".tex"):
            tex_file_path = os.path.join(input_directory, filename)
            table_count, figure_count = process_tex_file(
                tex_file_path,
                output_directory,
                table_count,
                figure_count,
                input_directory,
            )


def process_tex_file(tex_file_path, output_directory, table_count, figure_count, input_directory):
    with open(tex_file_path, "r") as file:
        latex_content = file.read()

    walker = LatexWalker(latex_content)
    nodes, _, _ = walker.get_latex_nodes(pos=0)

    table_count, figure_count = process_nodes(nodes, tex_file_path, output_directory, table_count, figure_count, input_directory, latex_content)
    return table_count, figure_count

def process_nodes(nodes, tex_file_path, output_directory, table_count, figure_count, input_directory, latex_content):
    for node in nodes:
        if isinstance(node, LatexEnvironmentNode):
            if node.environmentname in ["figure", "figure*"]:
                figure_count = process_figure(node, tex_file_path, output_directory, input_directory, figure_count)
            elif node.environmentname == "table":
                table_count = process_table(node, output_directory, table_count, latex_content)
            # Recursively process child nodes
            table_count, figure_count = process_nodes(node.nodelist, tex_file_path, output_directory, table_count, figure_count, input_directory, latex_content)
        elif isinstance(node, LatexMacroNode) and node.macroname == "includegraphics":
            figure_count = process_standalone_figure(node, tex_file_path, output_directory, input_directory, figure_count)
        # Add other conditions as needed
    return table_count, figure_count


def process_standalone_figure(node, tex_file_path, output_directory, input_directory, figure_count):
    fig_path = extract_figure_path_from_macro(node, input_directory)
    if fig_path:
        # Assuming no caption for standalone figures
        save_figure(fig_path, f"figure_{figure_count}", "", output_directory)
        figure_count += 1
    return figure_count


def extract_figure_path_from_macro(node, input_dir):
    if node.nodeargd and node.nodeargd.argnlist and len(node.nodeargd.argnlist) > 0:
        fig_path = node.nodeargd.argnlist[0].nodelist[0].latex_verbatim().strip()
        full_path = os.path.join(input_dir, fig_path)
        if os.path.isfile(full_path):
            return full_path
    return None


def process_figure(
    node, tex_file_path, output_directory, input_directory, figure_count
):
    fig_paths = extract_figure_paths(node, input_directory)
    caption = extract_caption(node)
    if fig_paths:
        save_combined_figure(
            fig_paths, f"figure_{figure_count}", caption, output_directory
        )
        figure_count += 1
    return figure_count


def extract_caption(node):
    caption = ""
    for n in node.nodelist:
        if isinstance(n, LatexMacroNode) and n.macroname == "caption":
            if n.nodeargd and n.nodeargd.argnlist and len(n.nodeargd.argnlist) > 0:
                caption_nodes = n.nodeargd.argnlist[0].nodelist
                caption = "".join(subnode.latex_verbatim() for subnode in caption_nodes)
                break
    print("Extracted caption: ", caption)  # Debugging line
    return caption


def save_combined_figure(fig_paths, label, caption, output_directory):
    combined_image_path = os.path.join(output_directory, f"{label}.png")
    caption_path = os.path.join(output_directory, f"{label}_caption.txt")
    # Combine images (you may need to adjust this part based on how you want to combine them)
    combine_images(fig_paths, combined_image_path)
    # Save caption
    with open(caption_path, "w") as cap_file:
        cap_file.write(caption)


def convert_pdf_to_image(pdf_filename, image_filename):
    # The following command adds a white background and trims the image.
    # You might need to adjust the "-trim" and "-border" options based on your specific needs.
    cmd = [
        "convert",
        "-density",
        "300",
        pdf_filename,
        "-background",
        "white",
        "-flatten",
        "-trim",
        "+repage",
        "-bordercolor",
        "white",
        "-border",
        "10x10",
        image_filename,
    ]
    subprocess.run(cmd)


def combine_images(image_paths, output_path):
    images = []
    for path in image_paths:
        print(path)
        if path.lower().endswith(".pdf"):
            path = path.replace("./", "")
            convert_pdf_to_image(path, path.replace(".pdf", ".png"))
            img = Image.open(path.replace(".pdf", ".png"))
            if img:
                images.append(img)
        else:
            images.append(Image.open(path))

    # Find the total width and the maximum height
    total_width = max(img.width for img in images)
    total_height = sum(img.height for img in images)

    # Create a new image with the appropriate height and width
    combined_image = Image.new("RGB", (total_width, total_height))

    # Paste each image into the combined image
    y_offset = 0
    for img in images:
        combined_image.paste(img, (0, y_offset))
        y_offset += img.height

    # Save the combined image
    combined_image.save(output_path)


def extract_figure_paths(node, input_dir):
    paths = []

    # Define a regular expression pattern to match \includegraphics commands
    includegraphics_pattern = r"\\includegraphics(?:\[[^\]]*\])?\{(.*?)\}"

    # Search for the pattern in the node's LaTeX content
    matches = re.findall(includegraphics_pattern, node.latex_verbatim())
    if matches:
        # Extract the file paths from the matches
        file_paths = [match.strip() for match in matches]
        # Check if the file exists in the directory
        for path in file_paths:
            if os.path.isfile(path):
                return path
            else:
                # Check for similar file names in the directory
                directory = os.path.join(
                    input_dir, path.replace(os.path.basename(path), "")
                )
                similar_files = [
                    f
                    for f in os.listdir(directory)
                    if os.path.basename(path) in os.path.basename(f)
                ]
                if similar_files:
                    paths.append(os.path.join(directory, similar_files[0]))
    return paths if len(paths) > 0 else None


def process_table(node, output_directory, table_count, latex_content):
    table_content = extract_table_content(node, latex_content)
    table_tex = create_table_tex(table_content)
    output_filename = os.path.join(output_directory, f"table_{table_count}.tex")
    with open(output_filename, "w") as file:
        file.write(table_tex)
    compile_table_to_image(output_filename, table_count, output_directory)
    return table_count + 1


def extract_label_or_figure_path(node, macro_name):
    for n in node.nodelist:
        if isinstance(n, LatexMacroNode) and n.macroname == macro_name:
            if n.nodeargd and n.nodeargd.argnlist and len(n.nodeargd.argnlist) > 0:
                return n.nodeargd.argnlist[0].nodelist[0].latex_verbatim()
    return ""  # Return an empty string if the macro is not found


def extract_table_content(node, latex_content):
    start_pos = node.pos
    end_pos = node.pos + node.len
    return latex_content[start_pos:end_pos]


def create_table_tex(table_content):
    return f"""\\documentclass{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage[T1]{{fontenc}}
\\usepackage{{booktabs}}
\\usepackage{{array}}
\\usepackage{{tabularx}}
\\usepackage{{longtable}}
\\usepackage{{float}}
\\usepackage{{graphicx}}
\\usepackage{{caption}}
\\usepackage{{hyperref}}
\\usepackage{{multirow}}
\\usepackage{{geometry}}
\\geometry{{left=1cm, right=1cm, top=2cm, bottom=2cm}}
\\pagestyle{{empty}}
\\begin{{document}}
{table_content}
\\end{{document}}"""


def compile_table_to_image(tex_filename, label, output_directory):
    cmd = [
        "pdflatex",
        "-interaction=nonstopmode",
        "-output-directory",
        output_directory,
        tex_filename,
    ]
    subprocess.run(cmd)
    pdf_filename = os.path.join(output_directory, f"table_{label}.pdf")
    image_filename = os.path.join(output_directory, f"table_{label}.png")
    convert_pdf_to_image(pdf_filename, image_filename)


def convert_pdf_to_image(pdf_filename, image_filename):
    # The following command adds a white background and trims the image.
    # You might need to adjust the "-trim" and "-border" options based on your specific needs.
    cmd = [
        "convert",
        "-density",
        "300",
        pdf_filename,
        "-background",
        "white",
        "-flatten",
        "-trim",
        "+repage",
        "-bordercolor",
        "white",
        "-border",
        "10x10",
        image_filename,
    ]
    subprocess.run(cmd)


def save_figure(source_path, label, caption, output_directory):
    _, file_extension = os.path.splitext(source_path)
    destination_path = os.path.join(output_directory, f"{label}{file_extension}")
    caption_path = os.path.join(output_directory, f"{label}_caption.txt")
    if os.path.isfile(source_path):
        shutil.copy(source_path, destination_path)
        with open(caption_path, "w") as cap_file:
            cap_file.write(caption)
        print(f"Figure saved: {destination_path}")
        print(f"Caption saved: {caption_path}")
    else:
        print(f"Warning: Figure file not found at {source_path}")


if __name__ == "__main__":
    # Replace these with the paths to your input and output directories
    input_directory_path = "mistral"
    output_directory_path = "output"
    process_files_in_order(input_directory_path, output_directory_path)
