import mistune
import os

template_head = '''
<html><head><meta charset="UTF-8"><style>body { background: #000; color: #fff;
width: 30%; padding: 30px; line-height: 14pt; font-size: 9pt; font-family: monospace; } a { color: cyan; } #logo
{ margin-bottom: 100px } h1,h2,h3 { margin-top: 50px; }</style></head><body>
<img id="logo" src="./void-ansi2.png" />
<br /><br />
'''

template_foot = '''
</body></html>
'''

with open('./index.md', 'r') as file_input:
    with open('./index_.html', 'w') as file_output:
        content = file_input.read()
        markdown = mistune.markdown(content)
        html = template_head + markdown + template_foot
        file_output.write(html)
