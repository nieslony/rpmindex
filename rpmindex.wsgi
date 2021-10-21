#!/usr/bin/python3

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from rpmindex.web import create_app

def main():
    parser = argparse.ArgumentParser(description="Start baustelle from command line")
    parser.add_argument("--environment", "-e",
                        help="Flask environment",
                        default="production",
                        choices=["production", "development"]
                        )
    parser.add_argument("--config", "-c",
                        help="Custom configuration file",
                        default=""
                        )
    parser.add_argument("--listen", "-l",
                        help="Listen on given IP address",
                        default="localhost"
                        )
    parser.add_argument("--port", "-p",
                        help="TCP to listen on",
                        default=5000,
                        type=int,
                        )
    args = parser.parse_args()

    os.environ["FLASK_ENV"] = args.environment
    if "config" in args:
        os.environ["CONFIG_PATH"] = args.config

    app = create_app()
    app.logger.info("Created app from min function")
    app.run(host=args.listen, port=args.port)

if __name__ == "__main__":
    # run from command line
    main()
else:
    # run from wsgi
    my_dir = f"{os.path.dirname(__file__)}"

    args = {
        "static_folder": f"{my_dir}/static",
        "template_folder": f"{my_dir}/templates",
        }

    application = create_app(**args)
    application.default_config_path = f"{my_dir}/rpmindex.yml"
