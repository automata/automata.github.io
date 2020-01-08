import mistune
import os

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
      <link rel="stylesheet" href="style.css">
      <link rel="shortcut icon" href="favicon.ico" type="image/x-icon">
    </head>
    <body>
      <img id="logo" src="./void-ansi2.png" />
      <br /><br />
'''

template_foot = '''
    </body>
   </html>
'''

with open('./index.md', 'r') as file_input:
    with open('./index.html', 'w') as file_output:
        content = file_input.read()
        markdown = mistune.markdown(content, escape=False)
        html = template_head + markdown + template_foot
        file_output.write(html)
