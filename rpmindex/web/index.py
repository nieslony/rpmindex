import datetime
import flask
import operator
import os
import re
import rpm
import textwrap

import rpmindex.web.folder_index as folder_index

bp = flask.Blueprint("index", __name__)

@bp.route('/', defaults={'path': ''})
@bp.route('/<path:path>')
def index(path):
    app = flask.current_app
    while path.endswith("/"):
        path = path[:-1]
    folder_path = os.path.realpath(f"{app.repo_path}/{path}")

    folder_path = re.sub("/RPM-GPG-KEY-[^\-]+", "/RPM-GPG-KEY", folder_path)

    if folder_path.endswith(".repo"):
        return download_repo_file(path, folder_path)

    if os.path.isdir(folder_path):
        return dir_index(path, folder_path)
    if os.path.isfile(folder_path):
        return download_file(folder_path)

    app.logger.error(f"{folder_path} is neither file nor directory")
    return flask.abort(404)

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

########################################

def direntry_rpm(filepath):
    app = flask.current_app
    app.logger.info(f"{filepath} is RPM")
    fd = os.open(filepath, os.O_RDONLY)
    ts = rpm.ts()
    try:
        headers = ts.hdrFromFdno(fd)
        description = headers[rpm.RPMTAG_SUMMARY]
    except Exception as ex:
        app.logger.error(f"Error getting headers from {filepath} :{str(ex)}")
        description = ""
    os.close(fd)

    return description

def read_folder(folder, path):
    app = flask.current_app
    app.logger.info(f"Reading folder {folder}")
    repo_name =  app.config["repo"]["name"]
    files = []
    dirs = []
    if not path in ["/", ""]:
        while path.endswith("/"):
            path = path[:-1]
        dirs.append({
            "name": "..",
            "size": "",
            "modified": ""
            })
    folder_infos = app.config["repo"]["folderrnames"]
    for folder_info in sorted(folder_infos, key=operator.itemgetter("path")):
        p = folder_info["path"]
        if is_prefix_of(p, path):
            repo_name = folder_info["description"]
    try:
        for filename in os.listdir(folder):
            filepath = f"{folder}/{filename}"
            stat = os.stat(filepath)
            mod_time = datetime.datetime.fromtimestamp(stat.st_mtime)
            if os.path.isfile(filepath):
                if filename.endswith(".rpm"):
                    description = direntry_rpm(filepath)
                else:
                    app.logger.info(f"{filename} is not RPM")
                    description = ""

                files.append({
                    "name": filename,
                    "size": stat.st_size,
                    "modified": mod_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "description": description
                    })
            elif os.path.isdir(filepath):
                dirs.append({
                    "name": filename,
                    "size": stat.st_size,
                    "modified": mod_time.strftime("%Y-%m-%d %H:%M:%S"),
                    })
                if filename == "repodata":
                    # we are in a repo's root folder

                    files.append({
                        "name": f"{os.path.basename(folder)}.repo",
                        "size": "123",
                        "modified": mod_time.strftime("%Y-%m-%d %H:%M:%S"),
                        })
    except FileNotFoundError as ex:
        app.logger(str(ex))
        flask.abort(404)

    args = {
        "title": repo_name,
        "path": path,
        "files": sorted(files, key=operator.itemgetter("name")),
        "dirs": sorted(dirs, key=operator.itemgetter("name"))
        }
    return flask.render_template("index.html", **args)

