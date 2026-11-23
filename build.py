import json
import os
from shutil import make_archive

import valveexe

from totcommon.builder import builder
from src._constants import VERSION, NAME, ORGNAME, URL


SIDECAR_DIR = os.path.join('plugins', 'vgct')


def validate_sidecar(definition):
    """Check the stamped sidecar against VGCT's schema before it ships.

    A malformed sidecar is invisible here -- the exe builds, the zip is
    fine -- and only surfaces when someone loads the tool into a graph and
    it refuses. The schema lives in ``plugins/vgct/vgct.schema.json``,
    a copy of the published one; if it drifts, replace that file.

    Raises rather than warning: a package that cannot be loaded is not a
    package worth publishing.
    """
    schema_path = os.path.join(SIDECAR_DIR, 'vgct.schema.json')
    if not os.path.isfile(schema_path):
        print('warning: no schema at ' + schema_path +
              ', sidecar NOT validated')
        return

    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        print('warning: jsonschema is not installed, sidecar NOT validated '
              '(pip install -r requirements.txt)')
        return

    with open(schema_path, encoding='utf-8') as f:
        validator = Draft202012Validator(json.load(f))

    errors = sorted(validator.iter_errors(definition),
                    key=lambda e: list(e.absolute_path))
    if errors:
        for error in errors:
            where = '/'.join(str(part) for part in error.absolute_path)
            print('sidecar invalid at {}: {}'.format(where or '(root)',
                                                     error.message))
        raise SystemExit("sidecar does not satisfy VGCT's schema")

    print("sidecar validates against VGCT's schema")


def write_sidecar(exe_name, version):
    """Ship the VGCT sidecar next to the built binary and re-zip.

    The definition is authored by hand in
    ``plugins/vgct/<name>.vgct.json``; edit that file to change the tool's
    inputs/outputs/arguments. Here we only stamp the build-derived fields
    (version/name/id/executable) so they can never drift from the actual
    binary, then write the result beside the exe.
    """
    filename = exe_name + '.vgct.json'
    source = os.path.join(SIDECAR_DIR, filename)
    if not os.path.isfile(source):
        print('warning: sidecar source not found, skipping: ' + source)
        return

    with open(source, encoding='utf-8') as f:
        definition = json.load(f)

    definition['version'] = version
    definition['name'] = exe_name
    definition['id'] = exe_name.lower()
    definition['executable'] = {'value': exe_name + '.exe'}

    validate_sidecar(definition)

    dist_dir = os.path.join('dist', '{}-v{}'.format(exe_name, version))
    exe_dir = os.path.join(dist_dir, exe_name)
    with open(os.path.join(exe_dir, filename), 'w', encoding='utf-8') as f:
        json.dump(definition, f, indent=2, ensure_ascii=False)
        f.write('\n')

    try:
        os.remove(dist_dir + '.zip')
    except OSError:
        pass
    make_archive(dist_dir, 'zip', dist_dir)


# PyInstaller does not follow PEP 660 editable installs, so it silently builds
# an exe with no valveexe in it. Point it at the directory the package actually
# resolves to -- the local ValveEXE checkout while it is installed with
# `pip install -e`, site-packages otherwise -- so the build always ships the
# same code the env imports. builder() forwards these straight to PyInstaller.
valveexeRoot = os.path.dirname(os.path.dirname(os.path.abspath(valveexe.__file__)))
print('bundling valveexe from: ' + valveexeRoot)

builder(NAME, ORGNAME, URL, VERSION, ['-p', valveexeRoot])
write_sidecar(NAME, VERSION)
