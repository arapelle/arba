#!/usr/bin/env python
import argparse
import datetime
import os.path
import re
import sys
import tempfile
from pathlib import Path


class ProjectInfo:
    def __init__(self, name, external: bool):
        self.name = name
        self.version = None
        self.external = external
        self.arba_deps = list[str]()
        self.external_deps = list[str]()
        self.children = list[str]()

    @property
    def deps(self):
        return self.arba_deps + self.external_deps

    def name_and_version(self, sep='/'):
        return f"{self.name}{sep}{self.version}"

    def identity(self, fmt):
        match fmt:
            case "n": return self.name
            case "n/v": return self.name_and_version()
            case "nv": return self.name_and_version("\n")
            case _: raise RuntimeError(f"Bad node name format: {fmt}")

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
        parser = argparse.ArgumentParser(prog='generate_project_info_files')
        parser.add_argument('-o', '--graph-orientation', choices=["RL", "LR", "BT", "TB"], default="RL",
                            help="Orientation of the dependency graph in SVG.")
        parser.add_argument('-n', '--node-format', choices=["n", "n/v", "nv"], default="n",
                            help="Node name format (Name, Name/Version, Name\\nVersion.")
        parser.add_argument('--node-fs', default="13", help="Node font size.")
        parser.add_argument('output_dir')
        args = parser.parse_args()
        self.__graph_orientation = args.graph_orientation
        self.__node_format = args.node_format
        self.__node_fs = args.node_fs
        self.__output_dir = Path(args.output_dir)
        print(f"args: {args}")
        self.projects = dict[str, ProjectInfo]()
        self.root_project = ""

    def run(self):
        self.__build_project_graph()
        project_seq = []
        self.__visit_project_graph(lambda pj: project_seq.append(pj.name))
        self.__generate_project_dependency_seq(project_seq, self.__output_dir / "project_dependency_seq.txt")
        self.__generate_project_dependency_graph_svg(project_seq, self.__output_dir / "project_dependency_graph.svg")

    def __generate_project_dependency_seq(self, project_seq, seq_path):
        print(f"Generate the project sequence file: {seq_path}")
        with open(seq_path, "w") as file:
            file.write(" ".join([f"arba-{x}" for x in project_seq]))

    def __generate_project_dependency_graph_svg(self, project_seq, svg_path):
        gv_path = f"{tempfile.gettempdir()}/project_dependency_graph.gv"
        print(f"Generate the project dependency graph gv file: {gv_path}")
        self.__generate_project_dependency_graph_gv(project_seq, gv_path)
        print(f"Generate the project dependency graph svg file: {svg_path}")
        dot_path = os.getenv("DOT_PATH", "dot")
        # To generate svg: dot -Tsvg graph.gv > graph.svg
        os.system(f"{dot_path} -Tsvg {gv_path} > {svg_path}")

    def __generate_project_dependency_graph_gv(self, project_seq, gv_path):
        id_fmt = self.__node_format
        arrows = []
        arba_nodes = []
        external_nodes = set()
        for x in project_seq:
            pinfo = self.projects[x]
            arrows_to_deps = "\n".join([f'    "{pinfo.identity(id_fmt)}" -> "{self.projects[x].identity(id_fmt)}"' for x in pinfo.arba_deps])
            arrows_to_external_deps = "\n".join([f'    "{pinfo.identity(id_fmt)}" -> "{x}"' for x in pinfo.external_deps])
            arrows.extend([f"# {pinfo.name}:", arrows_to_deps, arrows_to_external_deps])
            if not pinfo.external:
                arba_nodes.append(f'"{pinfo.identity(id_fmt)}";')
                external_nodes.update(pinfo.external_deps)
        arrows = "\n".join(filter(None, arrows))
        arba_nodes = "".join(arba_nodes)
        external_nodes = "".join([f"{x} [style=radial, fillcolor=\"white:lightgrey\"];" for x in external_nodes])
        with open(gv_path, "w") as graph_file:
            content = f"""digraph G
{{
  rankdir = {self.__graph_orientation};
  graph [fontname = \"helvetica\"];
  node [style=radial, fillcolor=\"white:lightgreen\"];
  node [fontname=\"monospace\"; fontsize={self.__node_fs}];
  edge [fontname=\"helvetica\"];
  label = "arba dependency graph";
  # nodes
  {arba_nodes}
  {external_nodes}
  # arrows
{arrows}
}}
            """
            graph_file.write(content)

    def __visit_project_graph(self, visitor):
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

    def __build_project_graph(self):
        for path in self.PROJECT_PATH.glob("arba-????/"):
            project_feature_name = str(path)[-4:]
            self.projects[project_feature_name] = ProjectInfo(project_feature_name, False)
        for name, info in self.projects.items():
            self.__find_dependencies(self.PROJECT_PATH / f"arba-{name}", info)
        self.root_project = next(filter(lambda pj: len(pj.deps) == 0, self.projects.values())).name

    def __find_dependencies(self, path: Path, project_info: ProjectInfo):
        with open(f'{path}/CMakeLists.txt', 'r') as cmake_file:
            for line in cmake_file.readlines():
                dep_match = re.match(r"\s*find_package\(([a-zA-Z0-9-_]+)", line)
                if dep_match:
                    dependency = dep_match.group(1)
                    arba_dep_match = re.match(r"arba-([a-z]{4})", dependency)
                    if arba_dep_match:
                        arba_dep = arba_dep_match.group(1)
                        project_info.arba_deps.append(arba_dep)
                        self.projects.get(arba_dep).children.append(project_info.name)
                    else:
                        project_info.external_deps.append(dependency)
                    continue
                version_match = re.match(r"\s*set_project_semantic_version\(\"([0-9\.]+)\"", line)
                if version_match:
                    project_info.version = version_match.group(1)
                    continue

    def print_projects(self):
        for project in self.projects.values():
            print(project.to_str())
        print(self.root_project)


if __name__ == '__main__':
    generator = GenerateGraph()
    generator.run()
