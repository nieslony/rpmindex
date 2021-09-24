import datetime
import flask
import operator
import os
import rpm

bp = flask.Blueprint("index", __name__)

@bp.route('/', defaults={'path': ''})
@bp.route('/<path:path>')
def index(path):
    app = flask.current_app
    repo_path = os.path.realpath(app.config["repo"]["path"])
    full_path = os.path.realpath(f"{repo_path}/{path}")

    if os.path.isdir(full_path):
        app.logger.info(f"{full_path} is directory")
        return read_folder(full_path, path)
    elif os.path.isfile(full_path):
        app.logger.info(f"{full_path} is file")
        return download_file(full_path)
    else:
        app.logger.error(f"File or directory not found: {full_path}")
        return flask.abort(404)

def download_file(filename):
    app.logger.info("Streaming {filename}")
    return flask.send_file(filename)

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
                    app.logger.info(f"{filename} is RPM")
                    fd = os.open(filepath, os.O_RDONLY)
                    ts = rpm.ts()
                    try:
                        headers = ts.hdrFromFdno(fd)
                        description = headers[rpm.RPMTAG_SUMMARY]
                    except Exception as ex:
                        app.logger.error(f"Error getting headers from {filepath} :{str(ex)}")
                        description = ""
                    os.close(fd)
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

def is_prefix_of(path1, path2):
    while path1.startswith("/"):
        path1 = path1[1:]
    while path2.startswith("/"):
        path2 = path2[1:]
    while path1.endswith("/"):
        path1 = path2[:-1]
    while path2.endswith("/"):
        path2 = path2[:-1]
    path1_list = path1.split("/")
    path2_list = path2.split("/")
    for i in range(len(path1_list)):
        if path1_list[i] != path2_list[i]:
            return False
    return True
