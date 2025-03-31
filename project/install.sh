#!/usr/bin/env bash

working_dir=`pwd`

projects="hash" # "vrsn cppx core strn vlfs rsce evnt"
for project in $projects
do
    cd $working_dir
    arba_project="arba-$project"
    echofmt "{bold}{red}$arba_project"
    cd $arba_project
    rm -rf /tmp/local/build/
    cmake -P cmake/script/quick_install.cmake \ # && rm -rf /tmp/local/ && cmake_test_build example/basic_cmake_project
    (( $? == 0 )) && (bell&) || break
done
