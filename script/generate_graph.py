#!/usr/bin/env python
import datetime
import os.path
import re
from pathlib import Path


class ProjectInfo:
    def __init__(self, name):
        self.name = name
        self.arba_deps = list[str]()
        self.external_deps = list[str]()
        self.children = list[str]()

    @property
    def deps(self):
        return self.arba_deps + self.external_deps

    def arba_deps_str(self):
        return "\n".join([f"{self.name} -> {x}" for x in self.arba_deps])

    def external_deps_str(self):
        return "\n".join([f"{self.name} -> {x}" for x in self.external_deps])

    def deps_str(self):
        return "\n".join([self.arba_deps_str(), self.external_deps_str()])

    def to_str(self):
        return f"{self.name}: {self.arba_deps}, {self.external_deps}, {self.children}"

    def __str__(self):
        return self.name


class GenerateGraph:
    PROJECT_PATH = Path(os.path.realpath(Path(__file__).parent.parent / "project"))

    def __init__(self):
        self.projects = dict[str, ProjectInfo]()
        self.root_project = ""

    def run(self):
        print(datetime.datetime.now())
        self.build_project_graph()
        project_seq = []
        self.visit_project_graph(lambda pj: project_seq.append(pj.name))
        # print(f"seq = {project_seq}")
        self.make_graph_gv(project_seq)
        # self.print_projects()
        os.system("C:/msys/mingw64/bin/dot -Tsvg graph.gv > graph.svg")

    def make_graph_gv(self, project_seq):
        arba_arrows = "\n".join([f"# {self.projects[x].name}:\n{self.projects[x].arba_deps_str()}" for x in project_seq])
        external_arrows = "\n".join([f"# {self.projects[x].name}:\n{self.projects[x].external_deps_str()}" for x in project_seq])
        arba_nodes = ";".join([x for x in project_seq if x in self.projects])
        external_nodes = set()
        for x in project_seq:
            external_nodes.update(self.projects[x].external_deps)
        external_nodes_str = ";".join([f"{x} [style=radial, fillcolor=\"white:lightgrey\"]" for x in external_nodes])
        with open(f"./graph.gv", "w") as graph_file:
            content = f"""
# To generate svg: dot -Tsvg graph.gv > graph.svg

digraph G
{{
#  rankdir = LR;
  graph [fontname = \"helvetica\"];
  node [style=radial, fillcolor=\"white:lightgreen\"];
  node [fontname=\"monospace\"; fontsize=13];
  edge [fontname=\"helvetica\"];
  label = arba;
  # nodes
  {arba_nodes}
  {external_nodes_str}
  # arrows
{arba_arrows}
{external_arrows}
}}
            """
            graph_file.write(content)

    def visit_project_graph(self, visitor):
        visited = []
        project_queue = [self.root_project]
        while len(project_queue) > 0:
            current_project = project_queue[0]
            project_queue = project_queue[1:]
            if current_project in visited:
                continue
            current_project_info = self.projects.get(current_project)
            if sum(1 for x in current_project_info.arba_deps if x in visited) != len(current_project_info.arba_deps):
                continue
            visited.append(current_project)
            assert current_project_info is not None
            visitor(current_project_info)
            project_queue.extend(current_project_info.children)

    def build_project_graph(self):
        for path in self.PROJECT_PATH.glob("arba-????/"):
            project_feature_name = str(path)[-4:]
            self.projects[project_feature_name] = ProjectInfo(project_feature_name)
        for name, info in self.projects.items():
            self.find_dependencies(self.PROJECT_PATH / f"arba-{name}", info)
        self.root_project = next(filter(lambda pj: len(pj.deps) == 0, self.projects.values())).name

    def print_projects(self):
        for project in self.projects.values():
            print(project.to_str())
        print(self.root_project)

    def find_dependencies(self, path: Path, project_info: ProjectInfo):
        with open(f'{path}/CMakeLists.txt', 'r') as cmake_file:
            for line in cmake_file.readlines():
                dep_match = re.match(r"\s*find_package\(([a-zA-Z0-9-_]+) ", line)
                if dep_match:
                    dependency = dep_match.group(1)
                    arba_dep_match = re.match(r"arba-([a-z]{4})", dependency)
                    if arba_dep_match:
                        arba_dep = arba_dep_match.group(1)
                        project_info.arba_deps.append(arba_dep)
                        self.projects.get(arba_dep).children.append(project_info.name)
                    else:
                        project_info.external_deps.append(dependency)


def main():
    generator = GenerateGraph()
    generator.run()


if __name__ == '__main__':
    main()
