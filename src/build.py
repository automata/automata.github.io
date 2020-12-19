import mistune
import mistune_contrib_meta as mc
import os
import time
import shutil
from datetime import datetime

config = {
    "index_file": "./docs/index/index.html",
    "braindump_file": "/media/ssd/src/automata/braindump",
    "html_output": "/media/ssd/src/automata/automata.github.io/docs"
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
      <a class="logo" href="/">
<svg id="logo" xmlns="http://www.w3.org/2000/svg" width="200" height="200" version="1.1">
  <circle cx="100" cy="20" r="20" fill="#fff"></circle>
  <circle cx="20" cy="180" r="20" fill="#fff"></circle>
  <circle cx="180" cy="180" r="20" fill="#fff"></circle>
  <polygon points="100,20 20,180 180,180" style="fill:#000"></polygon> 
</svg>
      <!--<img id="logo" src="/static/void-ansi2.png" />--></a>
'''

template_foot = '''
    <div id="footer">
      <a class="logo" href='https://webring.xxiivv.com/#random' target='_blank'><img class="webring_icon" src='https://webring.xxiivv.com/icon.white.svg'/></a>
    </div>
    </body>
   </html>
'''

def build_html(md_file, html_file, has_meta=True, skip_private=True, footer=""):
    with open(md_file, 'r') as file_input:
        with open(html_file, 'w') as file_output:
            content = file_input.read()
            if has_meta:
                meta_data, content = mc.parse(content)
                if "Title" in meta_data.keys():
                    content_title = meta_data["Title"]
                    content = f"# {content_title}\n\n" + content
            markdown = mistune.markdown(content, escape=False)
            html = template_head + markdown + footer + template_foot
            file_output.write(html)


def is_private(md_file):
    with open(md_file, "r") as f:
        content = f.read()
        meta_data, _ = mc.parse(content)
        if "Public" not in meta_data.keys():
            return True
    return False


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

def convert_braindump(remove_output_folder=False):
    md_files = get_md_files(config["braindump_file"])

    if remove_output_folder:
        shutil.rmtree(config["html_output"])
        os.mkdir(config["html_output"])
    for md_file in md_files:
        file_name, mdf = md_file
        with open(mdf, "r") as f:
            name_only = file_name[:-3]
            output_folder = os.path.join(config["html_output"], name_only)
            if not is_private(mdf):
                if not os.path.isdir(output_folder):
                    os.mkdir(output_folder)
                output_file = os.path.join(output_folder, "index.html")
                build_html(mdf, output_file)


def build_index():
    index_folder = os.path.join(config["html_output"], "index")
    if not os.path.isdir(index_folder):
        os.mkdir(index_folder)
    content = "<div class='index_cols'>"
    files_path = sorted(os.listdir(config["braindump_file"]))
    for file in files_path:
        if file.endswith((".md")):
            if not is_private(os.path.join(config["braindump_file"], file)):
                name_only = file[:-3]
                content += f"<a href='/{name_only}'>{name_only}</a>\n"
    content += "</div>"
    with open(config["index_file"], "w") as f:
        html = template_head + content + template_foot
        f.write(html)
    return content

def main():
    convert_braindump()
    content_index = build_index()
    content_index = "<h1>Braindump</h1>" + content_index
    build_html("./index.md", "./docs/index.html", footer=content_index)

main()
