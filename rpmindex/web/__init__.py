import flask
import logging
import os
import yaml

from rpmindex.common.utils import dict_merge

def create_app():
    app = flask.Flask(__name__)
    app.logger.setLevel(logging.DEBUG)

    app.logger.info("Loading blueprints")
    import rpmindex.web.index
    app.register_blueprint(rpmindex.web.index.bp)

    @app.before_first_request
    def bfr():
        default_config_fn = f"{os.path.dirname(__file__)}/../../rpmindex.yml"
        app.logger.info(f"Loading default config from {default_config_fn}")
        with open(default_config_fn) as f:
            config = yaml.load(f, Loader=yaml.Loader)
        # app.logger.debug(config)

        custom_config_fn = flask.request.environ.get("CONFIG_PATH")
        if not custom_config_fn:
            custom_config_fn = os.environ.get("CONFIG_PATH")
        if custom_config_fn:
            app.logger.info(f"Loading custom config from {custom_config_fn}")
            try:
                with open(custom_config_fn) as f:
                    custom_config = yaml.load(f, Loader=yaml.FullLoader)
            except Exception as ex:
                app.logger.fatal(f"Cannot load custom config: {str(ex)}")
                return
            dict_merge(config, custom_config)
        else:
            app.logger.info("No custom config given, skipping.")
        app.config.update(**config)
        # app.logger.debug(config)

        app.logger.info("After startup initialization finished.")

    return app
