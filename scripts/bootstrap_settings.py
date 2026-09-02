#!/usr/bin/env python
"""Create topicalguide/settings.py from the template, with a fresh SECRET_KEY.

topicalguide/settings.py is gitignored, so a fresh checkout has none and the
project will not start until one exists. This performs the copy the README
describes, generating the secret locally rather than fetching one from a
website.

    python scripts/bootstrap_settings.py

Refuses to overwrite an existing settings.py unless --force is given.
"""

import argparse
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(REPO_ROOT, 'topicalguide', 'settings.py.template')
TARGET = os.path.join(REPO_ROOT, 'topicalguide', 'settings.py')
PLACEHOLDER = "SECRET_KEY = ''"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--force', action='store_true',
                        help='overwrite an existing settings.py')
    parser.add_argument('--debug', action='store_true',
                        help='set DEBUG = True, for local development')
    args = parser.parse_args(argv)

    if os.path.exists(TARGET) and not args.force:
        print('%s already exists; pass --force to overwrite it.' % TARGET)
        return 1

    with open(TEMPLATE) as f:
        text = f.read()

    if PLACEHOLDER not in text:
        print('%s no longer contains %r -- has the template changed?'
              % (TEMPLATE, PLACEHOLDER))
        return 1

    # Imported here so --help works without Django installed.
    from django.core.management.utils import get_random_secret_key
    text = text.replace(PLACEHOLDER,
                        "SECRET_KEY = '%s'" % get_random_secret_key())
    if args.debug:
        text = text.replace('DEBUG = False', 'DEBUG = True')

    with open(TARGET, 'w') as f:
        f.write(text)
    print('Wrote %s' % TARGET)
    return 0


if __name__ == '__main__':
    sys.exit(main())
