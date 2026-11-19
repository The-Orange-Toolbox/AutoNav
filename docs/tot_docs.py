"""Builds this tool's documentation website.

This file is shared, byte for byte, by every Orange Toolbox tool; nothing in
it is specific to one of them. Keep the copies identical, so every site looks
and reads the same: change one, copy it to the others.

Almost all the site is generated from what the repository already holds:

    README.md                       home, installation and development pages
    src/_constants.py               name, version, links
    src/__main__.py build_parser()  the command-line reference
    plugins/compilepal/*.json       the CompilePal reference
    plugins/vgct/<name>.vgct.json   the VGCT node reference
    GitHub releases                 the changelog (when reachable)

README sections map to pages like so: the intro and every ordinary section
go on the home page, "Installation" gets a page of its own, and the block
between the <!--- start txt omit --> markers (the parts left out of the
packaged readme.txt) becomes the development page. Markdown files in
docs/pages/ are added as extra pages, for anything the README cannot hold.

Usage:
    python docs/tot_docs.py build    write the site to site/
    python docs/tot_docs.py serve    live preview at http://127.0.0.1:8000

Anything after the command goes straight to mkdocs, e.g.
    python docs/tot_docs.py serve -a 127.0.0.1:4000
"""

import argparse
import html
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, 'docs')
STAGE = os.path.join(ROOT, 'build', 'docs')

# Every tool in the toolbox, for the cross-links between the sites. Add new
# tools here (in every copy of this file).
TOOLBOX = [
    ('AutoCube', 'Cubemap generation'),
    ('AutoNav', 'Nav mesh generation'),
    ('AutoPak', 'Asset discovery for bspzip'),
]

OMIT = re.compile(r'<!--- start txt omit -->(.*?)<!--- end txt omit -->', re.S)


# --------------------------------------------------------------------------
# Inputs

def load_constants():
    constants = {}
    with open(os.path.join(ROOT, 'src', '_constants.py'), encoding='utf-8') as f:
        exec(f.read(), constants)
    return constants


def repo_slug(url):
    match = re.match(r'https?://github\.com/([^/]+)/([^/]+?)/?$', url)
    if not match:
        raise SystemExit('URL in _constants.py is not a GitHub repo: ' + url)
    return match.group(1), match.group(2)


def load_parser(name):
    """build_parser() from src/__main__.py, without running the tool."""
    src = os.path.join(ROOT, 'src')
    sys.path.insert(0, src)
    spec = importlib.util.spec_from_file_location(
        'tot_cli', os.path.join(src, '__main__.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    parser = module.build_parser()
    parser.prog = name
    return parser


def load_json(*parts):
    path = os.path.join(ROOT, *parts)
    if not os.path.isfile(path):
        return None
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def fetch_releases(org, repo):
    """The repo's GitHub releases, newest first; None if unreachable."""
    request = urllib.request.Request(
        'https://api.github.com/repos/{}/{}/releases'.format(org, repo),
        headers={'Accept': 'application/vnd.github+json',
                 'User-Agent': 'tot-docs'})
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        request.add_header('Authorization', 'Bearer ' + token)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.load(response)
    except Exception as error:  # offline, rate limited, private...
        print('warning: could not fetch releases: {}'.format(error))
        return None


# --------------------------------------------------------------------------
# README

def split_sections(markdown):
    """(intro, [(title, body)]) split on level-2 headings."""
    parts = re.split(r'^## +(.+?)\s*$', markdown, flags=re.M)
    return parts[0], list(zip(parts[1::2], parts[2::2]))


def demote(markdown, levels):
    """Shift every heading down (positive) or up (negative) by levels."""
    def shift(match):
        depth = max(1, min(6, len(match.group(1)) + levels))
        return '#' * depth + ' '
    return re.sub(r'^(#{1,6}) ', shift, markdown, flags=re.M)


def read_readme():
    with open(os.path.join(ROOT, 'README.md'), encoding='utf-8') as f:
        text = f.read()

    development = '\n'.join(block.strip() for block in OMIT.findall(text))
    text = OMIT.sub('', text)

    text = re.sub(r'\A# .*\n', '', text)                 # the title
    text = re.sub(r'^Download: .*\n', '', text, flags=re.M)

    intro, sections = split_sections(text)
    return intro.strip(), sections, development


# --------------------------------------------------------------------------
# Markdown helpers

def cell(text):
    """Make free text safe inside a markdown table cell."""
    text = html.escape(str(text), quote=False)
    return text.replace('|', '\\|').replace('\n', ' ')


def sentence(text):
    """Capitalised and full-stopped, however the help string was written."""
    text = text.strip()
    if not text:
        return text
    text = text[0].upper() + text[1:]
    return text if text[-1] in '.!?)' else text + '.'


def github_breaks(markdown):
    """GitHub renders a single newline as a line break; MkDocs does not."""
    out, fenced = [], False
    for line in markdown.replace('\r\n', '\n').split('\n'):
        if line.lstrip().startswith('```'):
            fenced = not fenced
        out.append(line if fenced or not line.strip() else line + '  ')
    return '\n'.join(out)


def code(text):
    return '`{}`'.format(str(text).replace('|', '\\|'))


def table(header, rows):
    if not rows:
        return '_None._\n'
    lines = ['| ' + ' | '.join(header) + ' |',
             '|' + '|'.join('---' for _ in header) + '|']
    lines += ['| ' + ' | '.join(row) + ' |' for row in rows]
    return '\n'.join(lines) + '\n'


# --------------------------------------------------------------------------
# Pages

def page_home(c, intro, sections, released):
    url = c['URL']
    download = url + ('/releases/latest' if released else '/releases')
    out = ['# ' + c['NAME'], '', intro, '',
           '[Download the latest release]({})'
           '{{ .md-button .md-button--primary }}'.format(download),
           '[View on GitHub]({}){{ .md-button }}'.format(url), '']
    for title, body in sections:
        out += ['## ' + title, '', body.strip(), '']
    return '\n'.join(out)


def page_installation(body):
    return '# Installation\n\n' + demote(body.strip(), -1) + '\n'


def page_development(body):
    return '# Development\n\n' + body + '\n'


def describe_action(action):
    """(option cell, value cell, description cell) for one argparse action."""
    if action.option_strings:
        names = ', '.join(code(o) for o in action.option_strings)
    else:
        names = code(action.metavar or action.dest)

    value = ''
    if action.choices:
        value = ' \\| '.join(code(c) for c in action.choices)
    elif action.nargs != 0 and action.option_strings:
        metavar = action.metavar or action.dest.upper()
        value = code(metavar if not isinstance(metavar, tuple)
                     else ' '.join(metavar))

    notes = []
    if action.required and action.option_strings:
        notes.append('**Required.**')
    if (isinstance(action, argparse._AppendAction)
            and 'repeatable' not in (action.help or '').lower()):
        notes.append('Repeatable.')
    default = action.default
    if (default not in (None, False, '', [], argparse.SUPPRESS)
            and not action.required and action.nargs != 0):
        notes.append('Default: {}.'.format(code(default)))

    text = action.help or ''
    if action.help == argparse.SUPPRESS:
        return None
    text = sentence(text.replace('%(default)s', str(default)))
    description = cell(text)
    if notes:
        description = (description + ' ' + ' '.join(notes)).strip()
    return names, value, description


def page_cli(c, parser):
    name = c['NAME']
    usage = parser.format_usage().replace('usage: ', '', 1).strip()
    out = ['# Command line', '',
           cell(parser.description or ''), '',
           '```text', usage, '```', '']

    for group in parser._action_groups:
        rows = [row for row in map(describe_action, group._group_actions)
                if row]
        if not rows:
            continue
        title = group.title
        title = {'positional arguments': 'Positional arguments',
                 'options': 'Options',
                 'optional arguments': 'Options'}.get(title, title.capitalize())
        out += ['## ' + title, '',
                table(['Argument', 'Value', 'Description'], rows)]

    if parser.epilog:
        out += ['!!! note', '    ' + cell(parser.epilog), '']

    out += ['## Full help text', '',
            'Exactly what `{} --help` prints:'.format(name), '',
            '```text', parser.format_help().strip(), '```', '']
    return '\n'.join(out)


def page_compilepal(c, meta, parameters):
    name = c['NAME']
    out = ['# CompilePal', '',
           'The release ships a CompilePal plugin next to `{}.exe`. Copy the '
           'whole folder into `Compile Pal 02x.xx/Parameters`, restart '
           'CompilePal, and add **{}** with the "Add..." button. See '
           '[Installation](../installation.md).'.format(name, meta['Name']
                                                        if meta else name),
           '']
    if meta:
        out += ['## Step', '', table(['Field', 'Value'], [
            ['Name', code(meta.get('Name', ''))],
            ['Description', cell(meta.get('Description', ''))],
            ['Command line', code(meta.get('BasisString', ''))],
            ['Order', code(meta.get('Order', ''))],
            ['Warning', cell(meta.get('Warning', '')) or '—'],
        ])]
    if parameters is not None:
        rows = [[cell(p.get('Name', '')),
                 code(p.get('Parameter', '').strip()),
                 'yes' if p.get('CanHaveValue') else 'no',
                 cell(p.get('Description', ''))
                 + ((' ⚠ ' + cell(p['Warning'])) if p.get('Warning') else '')]
                for p in parameters]
        out += ['## Parameters', '',
                'Extra options you can tick in the CompilePal UI. Each one '
                'adds its flag to the command line; see the '
                '[command line reference](command-line.md) for what they do.',
                '', table(['Name', 'Flag', 'Takes a value', 'Description'],
                          rows)]
    return '\n'.join(out)


def page_vgct(c, sidecar):
    name = c['NAME']
    out = ['# VGCT', '',
           'The release ships `{0}.vgct.json` next to `{0}.exe`. It describes '
           'the tool as a VGCT node: what it takes in, what it hands on, and '
           'the arguments it exposes. '
           '[Download the definition]({0}.vgct.json).'.format(name), '']

    out += ['## Node', '', table(['Field', 'Value'], [
        ['ID', code(sidecar.get('id', ''))],
        ['Category', cell(sidecar.get('category', ''))],
        ['Workspace', code(sidecar.get('workspace', 'sandbox'))],
        ['Concurrency', cell('{limit} at a time ({group})'.format(
            **sidecar['concurrency'])) if 'concurrency' in sidecar else '—'],
    ]), cell(sidecar.get('description', '')), '']

    out += ['## Inputs', '', table(['Port', 'Type', 'Required', 'Description'], [
        [code(p['id']), code(p['type']), 'yes' if p.get('required') else 'no',
         cell(p.get('description', ''))]
        for p in sidecar.get('inputs', [])])]

    out += ['## Outputs', '', table(['Port', 'Type', 'Description'], [
        [code(p['id']), code(p['type']), cell(p.get('description', ''))]
        for p in sidecar.get('outputs', [])])]

    rows = []
    for a in sidecar.get('arguments', []):
        if a.get('positional'):
            flag = '_positional_'
        else:
            flag = code(a.get('flag', '')) if a.get('flag') else '—'
        kind = a['type']
        if a.get('enum'):
            kind += ': ' + ' \\| '.join(code(e) for e in a['enum'])
        elif a.get('pathKind'):
            kind += ' (' + a['pathKind'] + ')'
        notes = []
        if a.get('required'):
            notes.append('**Required.**')
        if 'default' in a:
            notes.append('Default: {}.'.format(code(a['default'])))
        binding = a.get('defaultBinding')
        if binding and binding.get('source') == 'port':
            notes.append('Fed by the input port.')
        elif binding and binding.get('value', {}).get('value') is not None:
            notes.append('Bound to {}.'.format(code(binding['value']['value'])))
        description = cell(a.get('description', ''))
        if a.get('warning'):
            description += ' ⚠ ' + cell(a['warning'])
        rows.append([cell(a.get('name', a['id'])), flag, kind,
                     (description + ' ' + ' '.join(notes)).strip()])
    out += ['## Arguments', '',
            table(['Name', 'Flag', 'Type', 'Description'], rows)]
    return '\n'.join(out)


def page_changelog(c, releases):
    url = c['URL']
    out = ['# Changelog', '']
    if releases is None:
        out += ['See the [release page]({}/releases) on GitHub.'.format(url)]
    elif not releases:
        out += ['No releases yet. Version {} is the next one.'.format(
            c['VERSION'])]
    for release in releases or []:
        if release.get('draft'):
            continue
        title = release.get('name') or release.get('tag_name')
        date = (release.get('published_at') or '')[:10]
        out += ['## [{}]({})'.format(title, release['html_url']), '',
                '_{}_'.format(date) if date else '', '',
                github_breaks(demote((release.get('body') or '').strip(), 2)),
                '']
    return '\n'.join(out)


# --------------------------------------------------------------------------
# Site

def mkdocs_config(c, extra_pages, org):
    name, url = c['NAME'], c['URL']
    site_url = 'https://{}.github.io/{}/'.format(org.lower(), name)

    nav = [{'Home': 'index.md'}, {'Installation': 'installation.md'}]
    nav += [{title: path} for title, path in extra_pages]
    nav += [{'Reference': [
        {'Command line': 'reference/command-line.md'},
        {'CompilePal': 'reference/compilepal.md'},
        {'VGCT': 'reference/vgct.md'},
    ]}]
    nav += [{'Development': 'development.md'},
            {'Changelog': 'changelog.md'}]
    others = [{tool: 'https://{}.github.io/{}/'.format(org.lower(), tool)}
              for tool, _ in TOOLBOX if tool != name]
    nav += [{'The Orange Toolbox': others}]

    return {
        'site_name': name,
        'site_description': '{} - {}'.format(name, c.get('DESCRIPTION', '')),
        'site_url': site_url,
        'repo_url': url,
        'repo_name': '{}/{}'.format(org, name),
        'edit_uri': '',
        'copyright': '{} · v{} · GPL-3.0'.format(c['ORGNAME'], c['VERSION']),
        'docs_dir': 'pages',
        'site_dir': os.path.join(ROOT, 'site'),
        'theme': {
            'name': 'material',
            'logo': 'assets/icon.png',
            'favicon': 'assets/icon.png',
            'icon': {'repo': 'fontawesome/brands/github'},
            'palette': [
                {'media': '(prefers-color-scheme: light)', 'scheme': 'default',
                 'primary': 'custom', 'accent': 'custom',
                 'toggle': {'icon': 'material/weather-night',
                            'name': 'Switch to dark mode'}},
                {'media': '(prefers-color-scheme: dark)', 'scheme': 'slate',
                 'primary': 'custom', 'accent': 'custom',
                 'toggle': {'icon': 'material/weather-sunny',
                            'name': 'Switch to light mode'}},
            ],
            'features': ['navigation.sections', 'navigation.footer',
                         'navigation.top', 'content.code.copy', 'search.highlight'],
        },
        'extra_css': ['assets/toolbox.css'],
        'extra': {'social': [{'icon': 'fontawesome/brands/github',
                              'link': 'https://github.com/' + org}],
                  'generator': False},
        'markdown_extensions': [
            'admonition', 'attr_list', 'md_in_html', 'tables',
            {'toc': {'permalink': True}},
            'pymdownx.details', 'pymdownx.superfences',
            {'pymdownx.highlight': {'anchor_linenums': False}},
            'pymdownx.inlinehilite',
        ],
        'nav': nav,
    }


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text.rstrip('\n') + '\n')


def icon_png(destination):
    """The tool icon as a PNG (browsers do not all draw .ico as a logo)."""
    source = os.path.join(ROOT, 'icon', 'icon.ico')
    try:
        from PIL import Image
        with Image.open(source) as image:
            largest = max(image.ico.sizes())
            image.ico.getimage(largest).save(destination)
    except Exception as error:
        print('warning: could not convert the icon ({}); using it as is'
              .format(error))
        shutil.copy(source, destination)


def stage():
    c = load_constants()
    org, _ = repo_slug(c['URL'])
    name = c['NAME']

    intro, sections, development = read_readme()
    c['DESCRIPTION'] = re.sub(r'\s+', ' ', intro.split('\n\n')[0]).strip()

    home, installation = [], None
    for title, body in sections:
        if title.strip().lower() == 'installation':
            installation = body
        else:
            home.append((title, body))

    shutil.rmtree(STAGE, ignore_errors=True)
    pages = os.path.join(STAGE, 'pages')

    releases = fetch_releases(org, name)
    released = releases is None or any(not r.get('draft') for r in releases)
    write(os.path.join(pages, 'index.md'),
          page_home(c, intro, home, released))
    write(os.path.join(pages, 'installation.md'),
          page_installation(installation or 'See the README.'))
    write(os.path.join(pages, 'development.md'),
          page_development(development or 'See the repository.'))

    write(os.path.join(pages, 'reference', 'command-line.md'),
          page_cli(c, load_parser(name)))
    write(os.path.join(pages, 'reference', 'compilepal.md'),
          page_compilepal(c, load_json('plugins', 'compilepal', 'meta.json'),
                          load_json('plugins', 'compilepal', 'parameters.json')))

    sidecar = load_json('plugins', 'vgct', name + '.vgct.json')
    if sidecar is not None:
        sidecar['version'] = c['VERSION']      # as build.py stamps it
        write(os.path.join(pages, 'reference', 'vgct.md'), page_vgct(c, sidecar))
        write(os.path.join(pages, 'reference', name + '.vgct.json'),
              json.dumps(sidecar, indent=2))

    write(os.path.join(pages, 'changelog.md'),
          page_changelog(c, releases))

    extra = []
    custom = os.path.join(DOCS, 'pages')
    for filename in sorted(os.listdir(custom)) if os.path.isdir(custom) else []:
        if filename.endswith('.md'):
            shutil.copy(os.path.join(custom, filename), pages)
            with open(os.path.join(custom, filename), encoding='utf-8') as f:
                heading = re.search(r'^# +(.+)$', f.read(), flags=re.M)
            extra.append((heading.group(1) if heading else filename[:-3],
                          filename))

    assets = os.path.join(pages, 'assets')
    os.makedirs(assets, exist_ok=True)
    shutil.copy(os.path.join(DOCS, 'toolbox.css'), assets)
    icon_png(os.path.join(assets, 'icon.png'))

    config = os.path.join(STAGE, 'mkdocs.yml')
    write(config, json.dumps(mkdocs_config(c, extra, org), indent=2))
    return config


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else 'build'
    if command not in ('build', 'serve'):
        raise SystemExit(__doc__)
    config = stage()
    args = [sys.executable, '-m', 'mkdocs', command, '-f', config]
    if command == 'build':
        args.append('--strict')
    args += sys.argv[2:]
    raise SystemExit(subprocess.call(args))


if __name__ == '__main__':
    main()
