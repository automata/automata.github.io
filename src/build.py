import mistune
import mistune_contrib_meta as mc
import os
import time
from datetime import datetime

config = {
    "index_file": "./archive.html",
    "braindump_file": "/media/ssd/src/automata/braindump",
    "html_output": "/media/ssd/src/automata/automata.github.io"
}

template_head = '''
<!DOCTYPE html>
  <html>
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <meta name="description" content="Vilson Vieira Personal Website">
      <meta name="keywords" content="Personal Website, Machine Learning, AI, Computational Creativity, Gamedev, Research, USP, Physics, CS">
      <meta name="author" content="Vilson Vieira">
      <title>Vilson Vieira</title>
      <link rel="stylesheet" href="/static/style.css">
      <link rel="shortcut icon" href="/static/favicon.ico" type="image/x-icon">
    </head>
    <body>
      <a href="/"><img id="logo" src="/static/void-ansi2.png" /></a>
      <br /><br />
'''

template_foot = '''
    </body>
   </html>
'''

def build_html(md_file, html_file, has_meta=True, skip_private=True):
    with open(md_file, 'r') as file_input:
        with open(html_file, 'w') as file_output:
            content = file_input.read()
            if has_meta:
                meta_data, content = mc.parse(content)
                if "Private" in meta_data.keys():
                    return
            markdown = mistune.markdown(content, escape=False)
            html = template_head + markdown + template_foot
            file_output.write(html)


def get_md_files(folder_path):
    md_files = []
    for root, folders, files in os.walk(folder_path):
        for name in files:
            if name.endswith((".md")):
                md_path = os.path.join(root, name)
                md_files.append((name, md_path))

    return md_files


def create_md_header(title="", author="Vilson Vieira", date=None, is_private=False):
    if date is None:
        date = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    if is_private:
        return f"Title: {title}\nAuthor: {author}\nDate: {date}\nPrivate: True\n\n# "
    return f"Title: {title}\nAuthor: {author}\nDate: {date}\n\n"

def convert_braindump():
    md_files = get_md_files(config["braindump_file"])

    for md_file in md_files:
        file_name, mdf = md_file
        with open(mdf, "r") as f:
            output_folder = config["html_output"]
            output_file = os.path.join(output_folder, f"{file_name[:-3]}.html")
            build_html(mdf, output_file)


def build_index():
    content = "<ul>"
    for file in os.listdir(config["html_output"]):
        if file.endswith((".html")):
            content += f"<li><a href='/{file}'>{file[:-5]}</a></li>\n"
    content += "</ul>"
    with open(config["index_file"], "w") as f:
        html = template_head + content + template_foot
        f.write(html)

def main():
    build_html("./index.md", "./index.html")
    convert_braindump()
    # Create index
    build_index()

main()
