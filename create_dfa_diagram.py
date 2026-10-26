"""Render the program's token DFA as a PNG and an editable SVG.

Only this optional diagram-generation script needs Pillow. The web app itself
continues to use Python's standard library exclusively.
"""

from pathlib import Path
import html
import math

from PIL import Image, ImageDraw, ImageFont


OUT = Path(__file__).resolve().parent / "diagrams"
WIDTH, HEIGHT = 2400, 1730
BG, PANEL, BORDER = "#111827", "#172131", "#344155"
ORANGE, TEXT, MUTED = "#FF9030", "#F2F4F8", "#AAB5C6"
GREEN, RED = "#8BDAB3", "#FF9292"
image = Image.new("RGB", (WIDTH, HEIGHT), BG)
draw = ImageDraw.Draw(image)
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
       '<title>Assignment statements recognizer: token DFA with dead state</title>',
       '<desc>Six grammar states and one absorbing dead state. A complete transition table defines every transition.</desc>',
       f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{BG}"/>']
FONT_DIR = Path("C:/Windows/Fonts")


def font(size, mono=False, bold=False):
    filename = "consolab.ttf" if mono and bold else "consola.ttf" if mono else "segoeuib.ttf" if bold else "segoeui.ttf"
    try:
        return ImageFont.truetype(str(FONT_DIR / filename), size)
    except OSError:
        return ImageFont.truetype("DejaVuSans.ttf", size)


def text(x, y, value, size=28, color=TEXT, center=False, mono=False, bold=False):
    selected = font(size, mono, bold)
    width = draw.textlength(value, font=selected)
    draw.text((x - width / 2 if center else x, y), value, font=selected, fill=color)
    family = "Consolas,monospace" if mono else "Segoe UI,Arial,sans-serif"
    svg.append(f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-family="{family}" font-weight="{700 if bold else 400}" dominant-baseline="text-before-edge" text-anchor="{"middle" if center else "start"}">{html.escape(value)}</text>')


def box(x, y, width, height, fill=PANEL, stroke=BORDER, radius=20):
    draw.rounded_rectangle((x, y, x + width, y + height), radius, fill=fill, outline=stroke, width=2)
    svg.append(f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')


def line(points, color=BORDER, width=3, dashed=False):
    if dashed:
        for a, b in zip(points, points[1:]):
            distance = math.dist(a, b)
            for start in range(0, int(distance), 18):
                end = min(start + 10, distance)
                draw.line([(a[0] + (b[0] - a[0]) * t / distance, a[1] + (b[1] - a[1]) * t / distance) for t in (start, end)], fill=color, width=width)
    else:
        draw.line(points, fill=color, width=width, joint="curve")
    pts = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
    dash = ' stroke-dasharray="10 8"' if dashed else ""
    svg.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round"{dash}/>')


def arrow(points, color=ORANGE, width=4, dashed=False):
    line(points, color, width, dashed)
    end, previous = points[-1], points[-2]
    angle = math.atan2(end[1] - previous[1], end[0] - previous[0])
    corners = [end, (end[0] - 18 * math.cos(angle - .43), end[1] - 18 * math.sin(angle - .43)),
               (end[0] - 18 * math.cos(angle + .43), end[1] - 18 * math.sin(angle + .43))]
    draw.polygon(corners, fill=color)
    svg.append(f'<polygon points="{" ".join(f"{x:.2f},{y:.2f}" for x, y in corners)}" fill="{color}"/>')


def curve(start, c1, c2, end, color=ORANGE):
    points = []
    for i in range(101):
        t, u = i / 100, 1 - i / 100
        points.append(tuple(u**3 * start[j] + 3 * u*u*t * c1[j] + 3*u*t*t * c2[j] + t**3 * end[j] for j in (0, 1)))
    arrow(points, color)


def state(x, y, name, caption=None, color=ORANGE, accept=False):
    radius = 63
    draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill=BG, outline=color, width=4)
    svg.append(f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{BG}" stroke="{color}" stroke-width="4"/>')
    if accept:
        draw.ellipse((x-radius+10, y-radius+10, x+radius-10, y+radius-10), outline=color, width=3)
        svg.append(f'<circle cx="{x}" cy="{y}" r="{radius-10}" fill="none" stroke="{color}" stroke-width="3"/>')
    text(x, y-27, name, 40, color, center=True, mono=True, bold=True)
    if caption:
        text(x, y-117, caption, 20, MUTED, center=True, mono=True)


def build():
    text(100, 62, "ASSIGNMENT STATEMENTS RECOGNIZER", 21, ORANGE, mono=True, bold=True)
    text(100, 109, "Deterministic finite automaton", 62, bold=True)
    text(100, 194, "Token-based DFA  /  required datatype: int  /  includes the absorbing dead state", 28, MUTED)
    line([(100, 264), (2300, 264)])
    text(100, 300, "VALID PATH", 20, ORANGE, mono=True, bold=True)
    text(2015, 300, "Only q5 accepts", 24, GREEN)

    xs, y = [210, 605, 1000, 1395, 1790, 2185], 463
    arrow([(100, y), (xs[0]-68, y)], TEXT)
    labels = ["INT", "ID", "=", "NUM or ID", ";"]
    for i, label in enumerate(labels):
        arrow([(xs[i]+68, y), (xs[i+1]-68, y)])
        text((xs[i]+xs[i+1])/2, y-57, label, 30, ORANGE, center=True, mono=True, bold=True)
    captions = ["START", "DATATYPE READ", "IDENTIFIER READ", "EXPECT OPERAND", "OPERAND READ", "ACCEPT"]
    for i, (x, caption) in enumerate(zip(xs, captions)):
        state(x, y, f"q{i}", caption, GREEN if i == 5 else ORANGE, i == 5)
    # Reading an operator returns to the same operand-expecting state.
    curve((xs[4], y+67), (xs[4], 728), (xs[3], 728), (xs[3], y+67))
    text(1592, 707, "OP: +  -  *  /", 29, ORANGE, center=True, mono=True)
    text(1592, 751, "Repeat for additional operands", 21, MUTED, center=True)

    box(100, 825, 2200, 190, fill="#231F2B", stroke="#694251")
    text(133, 851, "DEAD STATE / DEADLOCK", 20, RED, mono=True, bold=True)
    text(133, 891, "Every unlisted transition from any state goes to qD.", 31, TEXT)
    text(133, 941, "Invalid characters also enter qD. Once there, all remaining input stays there.", 24, MUTED)
    arrow([(1450, 918), (1772, 918)], RED, dashed=True)
    text(1608, 867, "otherwise", 25, RED, center=True, mono=True)
    state(1843, 918, "qD", color=RED)
    curve((1891, 878), (2078, 755), (2078, 1081), (1891, 959), RED)
    text(2115, 875, "ANY TOKEN", 23, RED, center=True, mono=True)
    text(2115, 912, "self-loop", 21, MUTED, center=True)

    text(100, 1064, "COMPLETE TRANSITION TABLE", 21, ORANGE, mono=True, bold=True)
    text(100, 1103, "All transitions are defined. OTHER includes invalid characters.", 23, MUTED)
    box(100, 1156, 1360, 422, radius=14)
    headers = ["STATE", "INT", "ID", "NUM", "=", "OP", ";", "OTHER"]
    col_widths = [191, 167, 167, 167, 167, 167, 167, 167]
    centers, pos = [], 100
    for width in col_widths:
        centers.append(pos+width/2)
        pos += width
    for x, label in zip(centers, headers):
        text(x, 1171, label, 23, MUTED, center=True, mono=True, bold=True)
    line([(100, 1210), (1460, 1210)])
    transitions = {
        "q0": {"INT": "q1"}, "q1": {"ID": "q2"}, "q2": {"=": "q3"},
        "q3": {"ID": "q4", "NUM": "q4"}, "q4": {"OP": "q3", ";": "q5"},
        "q5": {}, "qD": {},
    }
    for index, (name, mapping) in enumerate(transitions.items()):
        row_y = 1220 + index*50
        text(centers[0], row_y, name + (" *" if name == "q5" else ""), 25,
             GREEN if name == "q5" else RED if name == "qD" else TEXT, center=True, mono=True, bold=True)
        for x, symbol in zip(centers[1:], headers[1:]):
            destination = mapping.get(symbol, "qD")
            text(x, row_y, destination, 25, RED if destination == "qD" else ORANGE, center=True, mono=True)
    text(100, 1596, "* Accept only when input ends in q5. Ending in any other state rejects.", 23, MUTED)

    text(1520, 1064, "TOKEN LEGEND", 21, ORANGE, mono=True, bold=True)
    legend = [
        ("INT", 'The exact keyword "int"'),
        ("ID", "L(L | D)*, except the keyword int"),
        ("NUM", "D+  (one or more digits)"),
        ("L / D", "L = a-z or A-Z; D = 0-9"),
        ("OP", "One of +, -, *, /"),
    ]
    for index, (label, detail) in enumerate(legend):
        at_y = 1123 + index*67
        text(1520, at_y, label, 23, ORANGE, mono=True, bold=True)
        text(1668, at_y, detail, 23, TEXT)
    text(1520, 1480, "Lexer skips spaces, tabs, and line breaks", 24, MUTED)
    text(1520, 1518, "between tokens. It never splits a name", 24, MUTED)
    text(1520, 1556, "or number; tokens use maximal matching.", 24, MUTED)
    line([(100, 1650), (2300, 1650)])
    text(100, 1670, "GRAMMAR   int identifier = operand (operator operand)* ;", 24, TEXT, mono=True)
    OUT.mkdir(exist_ok=True)
    image.save(OUT / "assignment-dfa.png", optimize=True)
    (OUT / "assignment-dfa.svg").write_text("\n".join(svg + ["</svg>"]), encoding="utf-8")
    print(OUT / "assignment-dfa.png")
    print(OUT / "assignment-dfa.svg")


if __name__ == "__main__":
    build()
