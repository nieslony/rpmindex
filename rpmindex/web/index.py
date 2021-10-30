import datetime
import flask
import operator
import os
import re
import rpm
import textwrap
import http

import rpmindex.web.folder_index as folder_index
from rpmindex.common.utils import is_prefix_of

bp = flask.Blueprint("index", __name__)

@bp.route('/', defaults={'path': ''})
@bp.route('/<path:path>')
def index(path):
    app = flask.current_app
    while path.endswith("/"):
        path = path[:-1]
    folder_path = os.path.realpath(f"{app.repo_path}/{path}")
    if not is_prefix_of(app.repo_path, folder_path):
        app.logger.error(
            f"Requiested folder {folder_path} is outsite repository {app.repo_path}"
            )
        return flask.abort(http.HTTPStatus.NOT_FOUND.value)

    folder_path = re.sub("/RPM-GPG-KEY-[^\-]+", "/RPM-GPG-KEY", folder_path)

    if folder_path.endswith(".repo"):
        return download_repo_file(path, folder_path)

    if os.path.isdir(folder_path):
        return dir_index(path, folder_path)
    if os.path.isfile(folder_path):
        return download_file(folder_path)

    app.logger.error(f"{folder_path} is neither file nor directory")
    return flask.abort(http.HTTPStatus.NOT_FOUND.value)

def dir_index(path, full_path):
    app = flask.current_app
    fi = folder_index.FolderIndex(path, full_path)
    fi.read()

    args = {
        "title": app.repo_name,
        "path": path,
        "files": sorted(fi.files, key=lambda x: x.name),
        "dirs": sorted(fi.dirs, key=lambda x: x.name)
        }
    return flask.render_template("index.html", **args)

def download_file(filename):
    app = flask.current_app
    app.logger.info(f"Streaming {filename}")
    return flask.send_file(filename)

def download_repo_file(path, full_path):
    app = flask.current_app
    dirname = os.path.dirname(full_path)

    if not os.path.isdir(f"{dirname}/repodata"):
        app.logger.error(f"There's no repodata in {dirname} => no .repo")
        return flask.abort(404)

    basename = os.path.basename(full_path)
    repo_file_name = f"{app.repo_name_encoded}.repo".lower()
    if basename != repo_file_name:
        app.logger.info(f"Filename {basename} doesn't match {repo_file_name}")
        return flask.abort(404)

    resp = flask.make_response(folder_index.repo_file_content(path))
    resp.mimetype = "text/plain"
    return resp
