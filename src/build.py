import mistune
import mistune_contrib_meta as mc
import os
import time
import shutil
import json

from datetime import datetime
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer, TextLexer
from pygments.formatters import HtmlFormatter

config_file = "./config.json"

PYGMENTS_FORMATTER = HtmlFormatter(style="github-dark", nowrap=True)


class HighlightRenderer(mistune.HTMLRenderer):
    def block_code(self, code, info=None):
        if info:
            lang = info.strip().split(None, 1)[0]
            try:
                lexer = get_lexer_by_name(lang, stripall=True)
            except Exception:
                lexer = TextLexer()
        else:
            lexer = TextLexer()
        highlighted = highlight(code, lexer, PYGMENTS_FORMATTER)
        return f'<pre><code class="highlight">{highlighted}</code></pre>\n'


_md = mistune.create_markdown(renderer=HighlightRenderer(escape=False))


def render_markdown(text):
    return _md(text)

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
      <link rel="stylesheet" href="/static/syntax.css">
      <link rel="shortcut icon" href="/static/favicon.ico" type="image/x-icon">
    </head>
    <body>
      <a class="logo" href="/">
      <img id="logo" src="/static/void-logo-white.svg" /></a>
'''

template_foot = '''
    <div id="footer">
      <a class="logo" href='https://webring.xxiivv.com/#random' target='_blank'><img class="webring_icon" src='https://webring.xxiivv.com/icon.white.svg'/></a>
      <a class="logo" href="http://www.catb.org/~esr/faqs/hacker-howto.html" target="_blank"><img class="webring_icon" src="/static/hacker_glider.svg"/></a>
    </div>
    </div>
    </body>
   </html>
'''


def load_config():
    with open("./config.json") as f:
        return json.load(f)


def build_html(md_file, html_file, has_meta=True, skip_private=True, inject_before=None, inject_content="", footer=""):
    with open(md_file, 'r') as file_input:
        with open(html_file, 'w') as file_output:
            content = file_input.read()
            if has_meta:
                meta_data, content = mc.parse(content)
                if "Title" in meta_data.keys():
                    content_title = meta_data["Title"]
                    content = f"# {content_title}\n\n" + content
            markdown = render_markdown(content)
            if inject_before and inject_content:
                markdown = markdown.replace(inject_before, inject_content + inject_before, 1)
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


def get_post_meta(md_file):
    with open(md_file, "r") as f:
        content = f.read()
        meta_data, _ = mc.parse(content)
        return meta_data


def convert_posts():
    posts_folder = "./posts"
    md_files = get_md_files(posts_folder)
    posts_meta = []

    for md_file in md_files:
        file_name, mdf = md_file
        meta = get_post_meta(mdf)
        if "Public" not in meta.keys():
            continue
        name_only = file_name[:-3]
        output_folder = os.path.join(config["html_output"], name_only)
        if not os.path.isdir(output_folder):
            os.mkdir(output_folder)
        output_file = os.path.join(output_folder, "index.html")
        build_html(mdf, output_file, has_meta=True)
        posts_meta.append({
            "title": meta.get("Title", name_only),
            "date": meta.get("Date", ""),
            "slug": name_only,
        })

    # Sort by date descending
    posts_meta.sort(key=lambda p: p["date"], reverse=True)
    return posts_meta


def build_index():
    index_folder = os.path.join(config["html_output"], "index")
    if not os.path.isdir(index_folder):
        os.mkdir(index_folder)
    content = "<div class='index_cols'>"
    entries = sorted(os.listdir(config["html_output"]))
    for entry in entries:
        entry_path = os.path.join(config["html_output"], entry)
        if os.path.isdir(entry_path) and entry != "index" and entry != "static":
            content += f"<a href='/{entry}'>{entry}</a>\n"
    content += "</div>"
    with open(config["index_file"], "w") as f:
        html = template_head + content + template_foot
        f.write(html)
    return content

def build_posts_section(posts_meta):
    if not posts_meta:
        return ""
    section = "<h1>Posts</h1>\n<div class='posts'>\n"
    for post in posts_meta:
        date_str = post["date"].split(" ")[0] if post["date"] else ""
        section += f"<div class='post-entry'><a href='/{post['slug']}'>{post['title']}</a><span class='post-date'>{date_str}</span></div>\n"
    section += "</div>\n"
    return section


def main():
    posts_meta = convert_posts()
    content_index = build_index()
    content_index = "<h1>Braindump</h1>" + content_index
    posts_section = build_posts_section(posts_meta)
    build_html("./index.md", "./docs/index.html",
               inject_before="<h1>Open Source Projects</h1>",
               inject_content=posts_section,
               footer=content_index)

config = load_config()
main()
