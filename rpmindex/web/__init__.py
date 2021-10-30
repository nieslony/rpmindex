import flask
import logging
import os
import re
import signal
import yaml

from rpmindex.common.utils import dict_merge, is_prefix_of
from rpmindex.web.repo_data import RepoData

class RpmIndexApp(flask.Flask):
    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)

        self._repo_data = {}
        self._default_config_path  = os.path.realpath(
            f"{os.path.dirname(__file__)}/../../rpmindex.yml"
            )

    @property
    def default_config_path(self):
        return self._default_config_path

    @default_config_path.setter
    def default_config_path(self, value):
        self._default_config_path = value

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
            app.logger.debug(f"Searching for repodata in {path}")
            if path in self._repo_data:
                app.logger.info(f"repodata for {folder_path} already loaded")
                mtime, repo_data = self._repo_data[path]
                stat = os.stat(f"{path}/repodata/repomd.xml")
                if stat.st_mtime > mtime:
                    app.logger.info(f"repomd.xml is newer than loaded one. Reloading")
                    repo_data = RepoData(path)
                    repo_data.load()
                    self._repo_data[path] = (stat.st_mtime, repo_data)
                return repo_data
            if os.path.isdir(f"{path}/repodata"):
                stat = os.stat(f"{path}/repodata/repomd.xml")
                repo_data = RepoData(path)
                repo_data.load()
                self._repo_data[path] = (stat.st_mtime, repo_data)
                return repo_data
            path = "/".join(path.split("/")[:-1])

        app.logger.info(f"No repodata found for folder {folder_path}")
        return None

def create_app(**kwargs):
    app = RpmIndexApp(__name__, **kwargs)
    app.logger.setLevel(logging.DEBUG)

    app.logger.info("Loading blueprints")
    import rpmindex.web.index
    app.register_blueprint(rpmindex.web.index.bp)

    @app.before_first_request
    def bfr():
        app.logger.info(f"Loading default config from {app.default_config_path}")
        with open(app.default_config_path) as f:
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
                os.kill(os.getpid(), signal.SIGKILL)
                return
            dict_merge(config, custom_config)
        else:
            app.logger.info("No custom config given, skipping.")
        app.config.update(**config)
        # app.logger.debug(config)

        app.logger.info("After startup initialization finished.")

    return app
