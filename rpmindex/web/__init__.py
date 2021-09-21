import flask

def create_app():
    app = flask.Flask(__name__)

    import rpmindex.web.index
    app.register_blueprint(rpmindex.web.index.bp)

    return app
