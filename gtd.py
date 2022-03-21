#!/usr/bin/python3

from functools import reduce
import os

import orgparse


def main():
    with open(os.path.expanduser("~/.gtd"), "r") as fh:
        sources = [line.strip() for line in fh.readlines()]
    project_list = ProjectList(sources)
    project_list.print()
    print()
    print(f"{len(project_list.projects)} projects")
    print(f"{project_list.n_actions()} next actions")
    print(f"{len(project_list.get_actionless_projects())} projects "
          f"without next actions")


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
                return list(map(lambda n: n.get_heading(format="raw"),
                                filter(lambda n: n.todo == "NEXT",
                                       child.children)))
        return []

    def print(self):
        print("\033[97;1m" + self.name + "\033[0m")
        if self.actions:
            for action in self.actions:
                print("\033[32;1m    ⤷  " + action + "\033[0m")
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
        return reduce(lambda total, project: total + len(project.actions),
                      self.projects, 0)

    def get_actionless_projects(self):
        return list(filter(lambda p: len(p.actions) == 0,
                           self.projects))

    def print(self):
        for project in self.projects:
            project.print()
            
    def scan_project_list(self, path):
        root = orgparse.load(path)
        project_lists = root.children
        current_projects = project_lists[0]
        for project in current_projects.children:
            self.projects.append(Project(project))
        return len(current_projects.children)
    
    def scan_directory(self, root_path):
        subdirs = list(map(
            lambda subdir: os.path.join(root_path, subdir),
            filter(lambda entry: os.path.isdir(os.path.join(root_path, entry)),
                   os.listdir(root_path))
            ))
        org_filenames = sorted(list(map(
            lambda subdir: os.path.join(subdir,
                                        os.path.basename(subdir) + ".org"),
            subdirs
        )))
        for org_filename in org_filenames:
            self.scan_project_org_file(org_filename)
        return len(org_filenames)
    
    def scan_project_org_file(self, filename: str):
        self.projects.append(Project(filename))


if __name__ == "__main__":
    main()
