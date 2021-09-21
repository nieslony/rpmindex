import flask
import os
import datetime
import rpm

bp = flask.Blueprint("index", __name__)

@bp.route('/', defaults={'path': ''})
@bp.route('/<path:path>')
def index(path):
    app = flask.current_app
    repo_path = os.path.realpath(app.config["repo"]["path"])
    repo_name =  app.config["repo"]["name"]
    folder = os.path.realpath(f"{repo_path}/{path}")

    app.logger.info(f"Reading folder {folder}")
    files = []
    dirs = []
    if not path in ["/", ""]:
        dirs.append({
            "name": "..",
            "size": "",
            "modified": ""
            })
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
        flask.abort(404)

    args = {
        "title": repo_name,
        "path": path,
        "files": files,
        "dirs": dirs
        }
    return flask.render_template("index.html", **args)
