import xml.dom.minidom
import gzip

import flask

from rpmindex.common.utils import is_prefix_of

class PackageVersion:
    def __init__(self, version_node):
        self._epoch = version_node.getAttribute("epoch")
        self._ver = version_node.getAttribute("ver")
        self._rel = version_node.getAttribute("rel")

    @property
    def epoch(self):
        return self._epoch

    @property
    def ver(self):
        return self._ver
    @property
    def rel(self):
        return self._rel

class PackageInfo:
    def __init__(self, dom_node):
        self._dom_node = dom_node

    @property
    def name(self):
        return self._get_tag_body("name")

    @property
    def arch(self):
        return self._get_tag_body("arch")

    @property
    def location(self):
        node = self._dom_node.getElementsByTagName("location")[0]
        return node.getAttribute("href")

    @property
    def version(self):
        return PackageVersion(self._dom_node.getElementsByTagName("version")[0])

    @property
    def summary(self):
        return self._get_tag_body("summary")

    @property
    def description(self):
        return self._get_tag_body("description")

    def _get_tag_body(self, tag_name):
        node = self._dom_node.getElementsByTagName(tag_name)[0]
        return node.firstChild.wholeText

class RepoData:
    def __init__(self, folder_path):
        self._folder_path = folder_path
        self._repo_data = {}

    def load(self):
        app = flask.current_app
        app.logger.info(f"Loading repo data from {self._folder_path}")

        repomd = xml.dom.minidom.parse(f"{self._folder_path}/repodata/repomd.xml")
        for data in repomd.getElementsByTagName("data"):
            if data.getAttribute("type") == "primary":
                primary_data_node = data.getElementsByTagName("location")[0]
                primary_data_fn = primary_data_node.getAttribute("href")
                break

        app.logger.info(f"Loading primary data from {primary_data_fn}")
        with gzip.open(f"{self._folder_path}/{primary_data_fn}", "rb") as xml_gz:
            content = xml_gz.read()

        parsed_xml = xml.dom.minidom.parseString(content)
        for package in parsed_xml.getElementsByTagName("package"):
            package_info = PackageInfo(package)
            self._repo_data[package_info.location] = package_info

    def package_info(self, file_path):
        if not is_prefix_of(self._folder_path, file_path):
            return None

        suffix = file_path[len(self._folder_path)+1:]
        return self._repo_data[suffix]
