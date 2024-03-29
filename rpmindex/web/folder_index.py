import datetime
import glob
import os
import re
import textwrap

import flask

class FolderEntry:
    def __init__(self):
        self._name = ""
        self._summary = ""
        self._description = ""
        self._modified = ""
        self._size = None
        self._repo_data = None

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value :str):
        self._name = value

    @property
    def description(self) -> str:
        return self._description

    @description.setter
    def description(self, value :str):
        self._description = value

    @property
    def summary(self):
        return self._summary

    @summary.setter
    def summary(self, value):
        self._summary = value

    @property
    def modified(self) -> str:
        return self._modified.strftime("%Y-%m-%d %H:%M:%S")

    @modified.setter
    def modified(self, value):
        self._modified = value

    @property
    def size(self) -> int:
        return self._size

    @size.setter
    def size(self, value :int):
        self._size = value

    def has_rpm_extra_info(self):
        return self._name.endswith(".rpm") and self._description

class FolderIndex:
    def __init__(self, path, folder_path):
        self._folder_path = folder_path
        self._path = path
        self._files = []
        self._dirs = []
        self._repo_data = None

    @property
    def files(self):
        return self._files

    @property
    def dirs(self):
        return self._dirs

    def read(self):
        app = flask.current_app
        self._repo_data = app.repo_data_for_folder(self._folder_path)

        if not self._path in ["/", ""]:
            self._add_dir_up()

        for entry_name in os.listdir(self._folder_path):
            entry_path = f"{self._folder_path}/{entry_name}"
            if not os.access(entry_path, os.R_OK):
                continue

            if os.path.isdir(entry_path):
                self._add_dir(entry_name)
            elif os.path.isfile(entry_path):
                self._add_file(entry_name)

    def _add_dir(self, entry_name):
        entry_path = f"{self._folder_path}/{entry_name}"
        stat = os.stat(entry_path)

        entry = FolderEntry()
        entry.name = entry_name
        entry.description = ""
        entry.size = 0
        entry.modified = datetime.datetime.fromtimestamp(stat.st_mtime)

        if entry_name == "repodata":
            self._add_repo_file()

        self._dirs.append(entry)

    def _add_file(self, entry_name):
        entry_path = f"{self._folder_path}/{entry_name}"
        stat = os.stat(entry_path)

        entry = FolderEntry()
        if entry_name.startswith("RPM-GPG-KEY-"):
            entry.name = self._make_key_name(entry_name)
        else:
            entry.name = entry_name

        if entry_name.endswith(".rpm") and self._repo_data:
            package_info = self._repo_data.package_info(entry_path)
            if package_info:
                entry.description = package_info.description.replace("\n", "<br>")
                entry.summary = package_info.summary
        entry.size = stat.st_size
        entry.modified = datetime.datetime.fromtimestamp(stat.st_mtime)

        self._files.append(entry)

    def _make_key_name(self, entry_name):
        app = flask.current_app
        return re.sub(
            r"^RPM-GPG-KEY-",
            f"RPM-GPG-KEY-{app.repo_name_encoded}-",
            entry_name
            )

    def repo_file_name(self):
        app = flask.current_app
        return f"{app.repo_name_encoded.lower()}.repo"

    def _add_repo_file(self):
        app = flask.current_app
        stat = os.stat(self._folder_path)

        entry = FolderEntry()
        entry.name = "repository.repo"
        entry.description = ""
        entry.size = len(self.repo_file_content())
        entry.modified = datetime.datetime.fromtimestamp(stat.st_mtime)
        self._files.append(entry)

        entry = FolderEntry()
        entry.name = self.repo_file_name()
        entry.description = ""
        entry.size = len(self.repo_file_content())
        entry.modified = datetime.datetime.fromtimestamp(stat.st_mtime)
        self._files.append(entry)

    def _add_dir_up(self):
        entry = FolderEntry()
        entry.name = ".."
        entry.size = 0
        entry.description = ""

        self._dirs.append(entry)

    def repo_file_content(self):
        app = flask.current_app
        repo_url = f"{flask.url_for('index.index', path=os.path.dirname(self._path), _external=True)}"

        key_files = glob.glob(f"{self._folder_path}/RPM-GPG-KEY-*")
        if key_files:
            key_file_name = os.path.basename(key_files[0])
            gpgkey = f"gpgkey={repo_url}/{self._make_key_name(key_file_name)}"
        else:
            gpgkey = ""

        content = f"""
            [{app.repo_name_encoded.lower()}]
            name={app.repo_name} - $releasever
            type=rpm
            enabled=1
            repo_gpgcheck=1
            baseurl={repo_url}
            {gpgkey}
            """

        return textwrap.dedent(content)
