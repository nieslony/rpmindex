import flask

bp = flask.Blueprint("index", __name__)

@bp.route("/")
def index():
    args = {
        "title": "The title"
            }
    return flask.render_template("index.html", **args)
