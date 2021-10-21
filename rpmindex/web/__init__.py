import flask
import logging
import os
import re
import yaml

from rpmindex.common.utils import dict_merge, is_prefix_of
from rpmindex.web.repo_data import RepoData

class RpmIndexApp(flask.Flask):
    def __init__(self, name):
        super().__init__(name)

        self._repo_data = {}

    @property
    def repo_path(self):
        return os.path.realpath(self.config["repo"]["path"])

    @property
    def repo_name(self):
        return self.config["repo"]["name"]

    @property
    def repo_name_encoded(self):
        remove_chars = r"[']"
        replace_chars = r"[ \-]"
        ret = self.repo_name
        ret = re.sub(remove_chars, "", ret)
        ret = re.sub(replace_chars, "_", ret)
        ret = re.sub(r"_+", "_", ret)
        return ret

    def repo_data_for_folder(self, folder_path):
        app = flask.current_app
        path = folder_path
        while is_prefix_of(self.repo_path, path):
            app.logger.debug(f"Searching for repodata ib {path}")
            if path in self._repo_data:
                app.logger.info(f"repodata for {folder_path} already loaded")
                return self._repo_data[path]
            if os.path.isdir(f"{path}/repodata"):
                repo_data = RepoData(path)
                repo_data.load()
                self._repo_data[path] = repo_data
                return repo_data
            path = "/".join(path.split("/")[:-1])

        app.logger.info(f"No repodata found for folder {folder_path}")
        return None

def create_app():
    app = RpmIndexApp(__name__)
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
