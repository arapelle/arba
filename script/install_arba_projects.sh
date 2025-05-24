#!/usr/bin/env bash

working_dir=`pwd`
script_dir=`bash_source_dir`
project_root_dir="${script_dir}/../project"

function abort_process {
    echofmt "{bold}{red}ERROR"
    tocsin -b
    exit 1
}

function install_project {
    local project_name="$1"
    local upper_project_name=${project_name//-/_}
    upper_project_name=${upper_project_name^^}
    local project_source_dir="$project_root_dir/$project_name"
    local project_build_dir="/tmp/local/build/${project_name}"
    command rm -rf $project_build_dir || abort_process 
    command mkdir -p $project_build_dir || abort_process
    command cmake \
        -DBUILD_${upper_project_name}_TESTS=On \
        -DBUILD_${upper_project_name}_EXAMPLES=On \
        -S $project_source_dir -B $project_build_dir || abort_process
    command cmake --build $project_build_dir || abort_process
    cd $project_build_dir || abort_process
    command ctest --progress --output-on-failure || abort_process
    cd $project_root_dir || abort_process
    command sudo cmake --install $project_build_dir || abort_process
    local test_package_build_dir="$project_build_dir/test_package"
    command cmake -S $project_source_dir/test_package -B $test_package_build_dir || abort_process
	command cmake --build $test_package_build_dir || abort_process
	# command $test_package_build_dir/test_package || abort_process
    ding -b
}

# projects=`cat ${script_dir}/../info/project_dependency_seq.txt`
projects="arba-cppx arba-rand arba-core arba-evnt arba-inis arba-hash 
    arba-meta arba-plug arba-strn arba-dirn arba-uuid arba-cryp arba-seri 
    arba-math arba-itru arba-stdx arba-wgen arba-vlfs arba-grid 
    arba-rsce arba-appt"
projects="arba-appt"
echofmt "Projects: {cyan}$projects"
for project in $projects
do
    echofmt "{bold}{yellow}# PROJECT $project"
    install_project $project
done
bell -b
