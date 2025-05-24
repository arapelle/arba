#!/usr/bin/env bash

script_dir=`bash_source_dir`
install_prefix_dir="/usr/local/lib/cmake"

projects=`cat ${script_dir}/../info/project_dependency_seq.txt`

for project in ${projects}
do
	uninstall_project_script="${install_prefix_dir}/${project}/uninstall.cmake"
	[[ -f $uninstall_project_script ]] && command sudo cmake -P $uninstall_project_script
done

command ls -1 "${install_prefix_dir}"
