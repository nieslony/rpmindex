#!/usr/bin/python

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from rpmindex.web import create_app

def main():
    app = create_app()
    app.run()

if __name__ == "__main__":
    # run from command line
    main()
else:
    # run from wsgi
    application = create_app()
