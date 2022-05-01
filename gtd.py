#!/usr/bin/env python3

# Copyright 2022 Pontus Lurcock (pont -at- talvi.net)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Produce a Getting Things Done next actions list from org files"""

from typing import Optional
from functools import reduce
import os
import argparse
import random
import yaml

import orgparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--randomize",
        "-r",
        action="store_true",
        help="display projects in random order",
    )
    parser.add_argument(
        "tag",
        type=str,
        nargs="?",
        default=None,
        help="only display actions with this tag",
    )
    args = parser.parse_args()
    config = read_config("~/.gtd")
    sources = map(expand_path, config["projects"])
    project_list = ProjectList(sources)
    project_list.print(args.randomize, args.tag)
    print()
    print(f"{len(project_list.projects)} projects")
    print(f"{project_list.n_actions()} next actions")

    n_actionless_projects = len(project_list.get_actionless_projects())
    if n_actionless_projects > 0:
        print(
            f"\033[91;1m{n_actionless_projects} projects without next actions"
        )
    inboxes = map(expand_path, config["inboxes"])
    inboxes_empty = True
    for inbox in inboxes:
        contents = os.listdir(inbox)
        n_items = len(contents)
        if n_items > 0:
            inboxes_empty = False
            print(f"\033[91;1m{n_items} items in {inbox}\033[0m")
    if inboxes_empty:
        print("All inboxes empty")


def read_config(path: str) -> dict:
    with open(expand_path(path), "r") as fh:
        config = yaml.safe_load(fh)
    return config


def expand_path(path: str) -> str:
    return os.path.expandvars(os.path.expanduser(path))


class Project:
    def __init__(self, node_or_path):
        self.actions = []
        if isinstance(node_or_path, str):
            self.name = os.path.splitext(os.path.basename(node_or_path))[0]
            if os.path.isfile(node_or_path):
                node = orgparse.load(node_or_path)
                self.actions = self._find_actions(node)
        else:
            node = node_or_path
            self.name = node.get_heading(format="raw")
            self.actions = self._find_actions(node)

    @staticmethod
    def _find_actions(node):
        for child in node.children:
            if child.heading == "Actions":
                return list(filter(lambda n: n.todo == "NEXT", child.children))
        return []

    def print(self, tag: Optional[str] = None):
        print("\033[97;1m" + self.name + "\033[0m")
        if self.actions:
            for action in self.actions:
                if tag is None or tag in action.tags:
                    print(
                        "\033[32;1m    ⤷  "
                        + action.get_heading(format="raw")
                        + "\033[0m"
                    )
        else:
            print("\033[91;1m    ⚠  No next actions!\033[0m")


class ProjectList:
    def __init__(self, paths):
        self.projects = []
        for path in paths:
            if os.path.isdir(path):
                self.scan_directory(path)
            else:
                self.scan_project_list(path)

    def n_actions(self):
        return reduce(
            lambda total, project: total + len(project.actions),
            self.projects,
            0,
        )

    def get_actionless_projects(self):
        return list(filter(lambda p: len(p.actions) == 0, self.projects))

    def print(self, randomize: bool = False, tag: Optional[str] = None):
        projects = (
            random.sample(self.projects, len(self.projects))
            if randomize
            else self.projects
        )
        for project in projects:
            project.print(tag)

    def scan_project_list(self, path):
        root = orgparse.load(path)
        project_lists = root.children
        current_projects = project_lists[0]
        for project in current_projects.children:
            self.projects.append(Project(project))
        return len(current_projects.children)

    def scan_directory(self, root_path):
        subdirs = list(
            map(
                lambda subdir: os.path.join(root_path, subdir),
                filter(
                    lambda entry: os.path.isdir(
                        os.path.join(root_path, entry)
                    ),
                    os.listdir(root_path),
                ),
            )
        )
        org_filenames = sorted(
            list(
                map(
                    lambda subdir: os.path.join(
                        subdir, os.path.basename(subdir) + ".org"
                    ),
                    subdirs,
                )
            )
        )
        for org_filename in org_filenames:
            self.scan_project_org_file(org_filename)
        return len(org_filenames)

    def scan_project_org_file(self, filename: str):
        self.projects.append(Project(filename))


if __name__ == "__main__":
    main()
