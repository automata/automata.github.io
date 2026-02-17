#!/bin/bash
slug="${1:-new}"
title="${slug//_/ }"
file="posts/${slug}.md"
date="$(date '+%Y-%m-%d %H:%M:%S')"

cat > "$file" <<EOF
Title: ${title}
Author: Vilson Vieira
Date: ${date}
Public: False

EOF

echo "Created ${file}"
