"""Give the snk dark snake an orange glow and a jack-o'-lantern head.

Usage: python3 enrich_snake.py dist/github-contribution-grid-snake-dark.svg
Edits the file in place. Safe to skip: if the head isn't found, the file is left as is.
"""
import re
import sys

path = sys.argv[1]
svg = open(path, encoding="utf-8").read()

GLOW = (
    '<defs><filter id="glow" x="-100%" y="-100%" width="300%" height="300%">'
    '<feGaussianBlur in="SourceGraphic" stdDeviation="3" result="b"/>'
    '<feFlood flood-color="#ff7518" flood-opacity="1"/>'
    '<feComposite in2="b" operator="in" result="g"/>'
    '<feMerge><feMergeNode in="g"/><feMergeNode in="g"/><feMergeNode in="g"/>'
    '<feMergeNode in="SourceGraphic"/></feMerge></filter></defs>'
)

HEAD = (
    '<g class="s s0"><g transform="translate(8 8) scale(1.3) translate(-8 -8.4)">'
    '<g filter="url(#glow)">'
    '<ellipse cx="4.6" cy="8.8" rx="4" ry="6" fill="#d9590f"/>'
    '<ellipse cx="11.4" cy="8.8" rx="4" ry="6" fill="#d9590f"/>'
    '<ellipse cx="8" cy="8.8" rx="4.6" ry="6.4" fill="#ff7518"/></g>'
    '<path d="M7.2 3.2 Q7.4 0.6 9.6 0.2 L9.9 1.1 Q8.6 1.6 8.8 3.2Z" fill="#4a7c2a"/>'
    '<path d="M3.6 8.1 L5.6 5.6 L6.6 8.1Z M9.4 8.1 L10.4 5.6 L12.4 8.1Z" fill="#fddf68"/>'
    '<path d="M3.4 10.2 Q8 14.2 12.6 10.2 L11.2 10.9 L10.4 10.1 L9.2 11.1 L8 10.2 '
    'L6.8 11.1 L5.6 10.1 L4.8 10.9Z" fill="#fddf68"/>'
    "</g></g>"
)

head_rect = re.compile(r'<rect class="s s0"[^>]*/>')
if not head_rect.search(svg) or "</style>" not in svg:
    print("Snake head not found; leaving the SVG unchanged.")
    sys.exit(0)

svg = svg.replace("</style>", ".s:not(.s0){filter:url(#glow)}</style>" + GLOW, 1)
svg = head_rect.sub("", svg, count=1)
svg = svg.replace("</svg>", HEAD + "</svg>")
open(path, "w", encoding="utf-8").write(svg)
print("Added the glow and the jack-o'-lantern head.")
