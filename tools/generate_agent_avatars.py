"""Generates the AI agent avatar SVGs (400x400, self-contained, no external assets).

Run:  python tools/generate_agent_avatars.py
Edit the AGENTS table below (colours, head shape, eyes, prop) to restyle an agent.
"""
import os, math

STYLE = '''<style>
@keyframes blink{0%,90%,100%{transform:scaleY(1)}94%{transform:scaleY(.08)}}
@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-7px)}}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.45}}
.eyes{transform-box:fill-box;transform-origin:center;animation:blink 5s infinite}
.prop{animation:bob 3.6s ease-in-out infinite}
.ant{animation:pulse 2.2s ease-in-out infinite}
@media (prefers-reduced-motion:reduce){.eyes,.prop,.ant{animation:none}}
</style>'''

OUT = r'D:\RD\rizendigital\static\assets\img\agents'
os.makedirs(OUT, exist_ok=True)

AGENTS = {
    # slug: (c1, c2, accent, head, eyes, antenna, ears, prop)
    'scout':  ('#4f7cff', '#2b3fd6', '#7df9ff', 'round',  'visor',   'single', 'pods',    'magnifier'),
    'atlas':  ('#12b5a6', '#0a7c8c', '#b6ff6a', 'square', 'bars',    'double', 'pods',    'gear'),
    'quill':  ('#a259ff', '#6a2fd6', '#ffd166', 'dome',   'happy',   'ring',   'pods',    'quill'),
    'pulse':  ('#ff5c8a', '#d61f69', '#ffe27a', 'round',  'dots',    'single', 'pods',    'chat'),
    'ledger': ('#ffb020', '#e07a00', '#fff2b3', 'square', 'cyclops', 'none',   'pods',    'target'),
    'vega':   ('#28c76f', '#12965a', '#c8ffd9', 'hex',    'visor',   'double', 'pods',    'chart'),
    'prism':  ('#ff7a45', '#d6336c', '#ffe066', 'dome',   'happy',   'ring',   'pods',    'prism'),
    'echo':   ('#36a3ff', '#1c6fe0', '#9bf0ff', 'round',  'dots',    'none',   'headset', 'bubbles'),
    'forge':  ('#6b7cff', '#3b2fb0', '#ff9f43', 'hex',    'bars',    'single', 'pods',    'code'),
}


def head_path(shape):
    # head spans x 105..295, y 88..258
    if shape == 'round':
        return '<rect x="108" y="92" width="184" height="164" rx="70" fill="url(#hg)"/>'
    if shape == 'square':
        return '<rect x="108" y="92" width="184" height="164" rx="36" fill="url(#hg)"/>'
    if shape == 'dome':
        return '<path d="M108 256 V170 C108 110 150 84 200 84 C250 84 292 110 292 170 V256 Q292 262 286 262 H114 Q108 262 108 256Z" fill="url(#hg)"/>'
    if shape == 'hex':
        return '<path d="M150 90 H250 L296 172 L250 256 H150 L104 172Z" fill="url(#hg)" stroke="url(#hg)" stroke-width="18" stroke-linejoin="round"/>'
    return ''


def eyes(style, acc):
    return _eyes(style, acc)


def _eyes(style, acc):
    plate = ('<rect x="134" y="140" width="132" height="86" rx="34" fill="#0b1030"/>'
             '<rect x="134" y="140" width="132" height="86" rx="34" fill="url(#gloss)"/>')
    g = f'filter="url(#glow)" fill="{acc}"'
    if style == 'visor':
        return plate + f'<ellipse cx="172" cy="183" rx="15" ry="19" {g}/><ellipse cx="228" cy="183" rx="15" ry="19" {g}/>' \
               f'<circle cx="177" cy="176" r="4.5" fill="#fff"/><circle cx="233" cy="176" r="4.5" fill="#fff"/>'
    if style == 'dots':
        return plate + f'<circle cx="172" cy="178" r="13" {g}/><circle cx="228" cy="178" r="13" {g}/>' \
               f'<circle cx="176" cy="173" r="4" fill="#fff"/><circle cx="232" cy="173" r="4" fill="#fff"/>' \
               f'<path d="M184 203 Q200 216 216 203" stroke="{acc}" stroke-width="5" fill="none" stroke-linecap="round" filter="url(#glow)"/>'
    if style == 'cyclops':
        return plate + f'<circle cx="200" cy="183" r="27" fill="none" stroke="{acc}" stroke-width="5" filter="url(#glow)"/>' \
               f'<circle cx="200" cy="183" r="14" {g}/><circle cx="205" cy="177" r="5" fill="#fff"/>'
    if style == 'bars':
        return plate + f'<rect x="153" y="165" width="34" height="13" rx="6.5" {g}/><rect x="213" y="165" width="34" height="13" rx="6.5" {g}/>' \
               f'<rect x="170" y="196" width="60" height="9" rx="4.5" {g} opacity=".9"/>'
    if style == 'happy':
        return plate + f'<path d="M156 188 Q172 165 188 188" stroke="{acc}" stroke-width="8" fill="none" stroke-linecap="round" filter="url(#glow)"/>' \
               f'<path d="M212 188 Q228 165 244 188" stroke="{acc}" stroke-width="8" fill="none" stroke-linecap="round" filter="url(#glow)"/>' \
               f'<path d="M180 204 Q200 222 220 204" stroke="{acc}" stroke-width="5" fill="none" stroke-linecap="round" filter="url(#glow)"/>'
    return plate


def wrap_eyes(s):
    marker = 'fill="url(#gloss)"/>'
    i = s.index(marker) + len(marker)
    return s[:i] + '<g class="eyes">' + s[i:] + '</g>'


def antenna(kind, acc):
    if kind == 'single':
        return f'<rect x="196" y="52" width="8" height="42" rx="4" fill="#1a2260"/><circle cx="200" cy="48" r="11" fill="{acc}" filter="url(#glow)"/>'
    if kind == 'double':
        return (f'<path d="M168 96 L152 56" stroke="#1a2260" stroke-width="8" stroke-linecap="round"/><circle cx="150" cy="52" r="9" fill="{acc}" filter="url(#glow)"/>'
                f'<path d="M232 96 L248 56" stroke="#1a2260" stroke-width="8" stroke-linecap="round"/><circle cx="250" cy="52" r="9" fill="{acc}" filter="url(#glow)"/>')
    if kind == 'ring':
        return f'<rect x="196" y="58" width="8" height="34" rx="4" fill="#1a2260"/><circle cx="200" cy="50" r="13" fill="none" stroke="{acc}" stroke-width="6" filter="url(#glow)"/>'
    return ''


def ears(kind, c2, acc):
    if kind == 'headset':
        return (f'<rect x="90" y="150" width="26" height="60" rx="13" fill="#1a2260"/><rect x="284" y="150" width="26" height="60" rx="13" fill="#1a2260"/>'
                f'<path d="M100 150 Q100 80 200 80 Q300 80 300 150" stroke="#1a2260" stroke-width="9" fill="none" stroke-linecap="round"/>'
                f'<path d="M300 200 Q300 240 262 246" stroke="#1a2260" stroke-width="7" fill="none" stroke-linecap="round"/><circle cx="256" cy="246" r="9" fill="{acc}" filter="url(#glow)"/>')
    return (f'<rect x="92" y="160" width="20" height="44" rx="10" fill="{c2}"/><rect x="288" y="160" width="20" height="44" rx="10" fill="{c2}"/>'
            f'<rect x="97" y="172" width="10" height="20" rx="5" fill="{acc}" opacity=".9"/><rect x="293" y="172" width="10" height="20" rx="5" fill="{acc}" opacity=".9"/>')


def prop(kind, acc):
    a = acc
    s = 'stroke-linecap="round" stroke-linejoin="round"'
    P = {
        'magnifier': f'<g transform="translate(300 80)"><circle cx="0" cy="0" r="26" fill="rgba(255,255,255,.14)" stroke="{a}" stroke-width="7"/><path d="M19 19 L40 40" stroke="{a}" stroke-width="9" {s}/><path d="M-11 -8 Q-3 -17 8 -13" stroke="#fff" stroke-width="4" fill="none" {s} opacity=".8"/></g>',
        'gear': '<g transform="translate(300 84)">' + ''.join(f'<rect x="-6" y="-38" width="12" height="16" rx="3" fill="{a}" transform="rotate({i*45})"/>' for i in range(8)) + f'<circle r="27" fill="{a}"/><circle r="11" fill="#0b1030"/></g>',
        'quill': f'<g transform="translate(298 84) rotate(28)"><path d="M0 -44 C26 -30 30 6 4 40 C-4 20 -22 -8 0 -44Z" fill="{a}"/><path d="M2 -34 L4 36" stroke="#0b1030" stroke-width="3" opacity=".45" {s}/></g><path d="M262 40 l4 10 10 4 -10 4 -4 10 -4 -10 -10 -4 10 -4z" fill="#fff" opacity=".9"/>',
        'chat': f'<g transform="translate(296 80)"><path d="M-30 -24 H30 a10 10 0 0 1 10 10 V12 a10 10 0 0 1 -10 10 H0 L-16 36 V22 H-30 a10 10 0 0 1 -10 -10 V-14 a10 10 0 0 1 10 -10Z" fill="{a}"/><path d="M0 9 c-14 -9 -14 -20 -6 -22 c4 -1 6 2 6 4 c0 -2 2 -5 6 -4 c8 2 8 13 -6 22z" fill="#d61f69"/></g>',
        'target': f'<g transform="translate(300 82)"><circle r="32" fill="none" stroke="{a}" stroke-width="7"/><circle r="19" fill="none" stroke="{a}" stroke-width="6" opacity=".85"/><circle r="7" fill="{a}"/><path d="M6 -6 L34 -34" stroke="#fff" stroke-width="5" {s}/><path d="M26 -34 H36 V-24" stroke="#fff" stroke-width="5" fill="none" {s}/></g>',
        'chart': f'<g transform="translate(300 82)"><rect x="-30" y="2" width="14" height="30" rx="4" fill="{a}" opacity=".8"/><rect x="-7" y="-14" width="14" height="46" rx="4" fill="{a}"/><rect x="16" y="-32" width="14" height="64" rx="4" fill="{a}"/><path d="M-32 -6 L-6 -24 L14 -16 L34 -40" stroke="#fff" stroke-width="4.5" fill="none" {s}/></g>',
        'prism': f'<g transform="translate(300 84)"><path d="M0 -34 L34 26 H-34Z" fill="rgba(255,255,255,.2)" stroke="#fff" stroke-width="5" {s}/><path d="M-46 -2 L-14 6" stroke="#fff" stroke-width="4" {s}/><path d="M14 8 L46 -8" stroke="#ff5f6d" stroke-width="5" {s}/><path d="M14 14 L46 4" stroke="#ffd166" stroke-width="5" {s}/><path d="M14 20 L46 16" stroke="#54e0a0" stroke-width="5" {s}/><path d="M14 26 L46 28" stroke="#5ab0ff" stroke-width="5" {s}/></g>',
        'bubbles': f'<g transform="translate(296 82)"><rect x="-36" y="-26" width="46" height="34" rx="12" fill="{a}"/><path d="M-22 8 v14 l14 -14z" fill="{a}"/><rect x="0" y="-2" width="42" height="30" rx="11" fill="#fff" opacity=".92"/><circle cx="12" cy="13" r="3.5" fill="#1c6fe0"/><circle cx="21" cy="13" r="3.5" fill="#1c6fe0"/><circle cx="30" cy="13" r="3.5" fill="#1c6fe0"/></g>',
        'code': f'<g transform="translate(300 84)"><path d="M-14 -22 L-36 0 L-14 22" stroke="{a}" stroke-width="9" fill="none" {s}/><path d="M14 -22 L36 0 L14 22" stroke="{a}" stroke-width="9" fill="none" {s}/><path d="M6 -28 L-6 28" stroke="#fff" stroke-width="7" {s}/></g>',
    }
    return P[kind]


def badge(kind, acc):
    """Small glyph on the chest plate."""
    return f'<circle cx="200" cy="332" r="13" fill="{acc}" opacity=".95" filter="url(#glow)"/><circle cx="200" cy="332" r="5" fill="#0b1030"/>'


def build(slug, c1, c2, acc, head, eye, ant, ear, pr):
    dots = ''.join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#fff" opacity="{o}"/>' for x, y, r, o in
                   [(52, 90, 3, .5), (70, 300, 2.5, .4), (352, 260, 3.5, .35), (40, 210, 2, .5), (340, 340, 2.5, .3), (110, 40, 2, .45)])
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" role="img" aria-label="{slug.title()} AI agent">
<defs>
{STYLE}
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="#0b1030"/></linearGradient>
<linearGradient id="hg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff"/><stop offset=".08" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient>
<linearGradient id="bodyg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient>
<linearGradient id="gloss" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".16"/><stop offset=".5" stop-color="#fff" stop-opacity="0"/></linearGradient>
<radialGradient id="halo" cx=".5" cy=".42" r=".55"><stop offset="0" stop-color="{acc}" stop-opacity=".45"/><stop offset="1" stop-color="{acc}" stop-opacity="0"/></radialGradient>
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<pattern id="grid" width="28" height="28" patternUnits="userSpaceOnUse"><path d="M28 0H0V28" fill="none" stroke="#fff" stroke-opacity=".07"/></pattern>
</defs>
<rect width="400" height="400" fill="url(#bg)"/>
<rect width="400" height="400" fill="url(#grid)"/>
<circle cx="200" cy="170" r="190" fill="url(#halo)"/>
<circle cx="70" cy="60" r="90" fill="{acc}" opacity=".08"/><circle cx="350" cy="380" r="120" fill="{c2}" opacity=".35"/>
{dots}
<g>
<path d="M62 400 C62 318 118 292 200 292 C282 292 338 318 338 400Z" fill="url(#bodyg)"/>
<path d="M62 400 C62 318 118 292 200 292 C282 292 338 318 338 400Z" fill="url(#gloss)"/>
<path d="M150 296 Q200 330 250 296" stroke="#0b1030" stroke-opacity=".35" stroke-width="10" fill="none" stroke-linecap="round"/>
<rect x="172" y="268" width="56" height="34" rx="14" fill="#1a2260"/>
<rect x="150" y="312" width="100" height="44" rx="16" fill="#0b1030" opacity=".85"/>
{badge(pr, acc)}
<rect x="164" y="346" width="72" height="5" rx="2.5" fill="{acc}" opacity=".55"/>
</g>
<g class="ant">{ant and antenna(ant, acc)}</g>
{ears(ear, c2, acc)}
{head_path(head)}
<path d="M120 112 Q150 96 190 96" stroke="#fff" stroke-opacity=".55" stroke-width="6" fill="none" stroke-linecap="round"/>
{wrap_eyes(eyes(eye, acc))}
<circle cx="126" cy="214" r="7" fill="{acc}" opacity=".35"/><circle cx="274" cy="214" r="7" fill="{acc}" opacity=".35"/>
<g class="prop">{prop(pr, acc)}</g>
</svg>
'''


for slug, params in AGENTS.items():
    svg = build(slug, *params)
    with open(os.path.join(OUT, slug + '.svg'), 'w', encoding='utf-8') as f:
        f.write(svg)
    print(slug, len(svg), 'bytes')
