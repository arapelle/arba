#!/usr/bin/env bash

projects=`find -maxdepth 1 -name "arba-????"`

feature_names=""
for project in ${projects}
do
    if [[ ! -e "$project/conanfile.py" ]]
    then
        continue
    fi
    feature_name=`echo $project | cut -d'-' -f2`
    feature_names="${feature_name};${feature_names}"
    deps=""
    grep_res=$(grep -oP "find_package\(arba-\K.{4}" $project/CMakeLists.txt)
    for dep in $grep_res
    do
        deps="$deps $dep"
    done
    deps=$(echo $deps|xargs)
    if [[ -n "$deps" ]]
    then
        echo "# $feature_name:"
        # echo "  deps: $deps"
        for dep in $deps
        do
            echo "  $feature_name -> $dep"
        done
    fi
done
echo
echo "$(echo $feature_names|xargs)"
