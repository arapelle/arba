#!/usr/bin/env bash

graph_filename="arba.gv"

echo "# To generate svg: dot -Tsvg graph.gv > graph.svg

digraph G
{
#  rankdir = LR;
  graph [fontname = \"helvetica\"];
  node [style=radial, fillcolor=\"white:lightgreen\"];
  node [fontname=\"monospace\"; fontsize=13];
  edge [fontname=\"helvetica\"];
  label = arba;
" > $graph_filename

projects=`find -maxdepth 1 -name "arba-????"`
feature_names=""
for project in ${projects}
do
    if [[ -e "$project/conanfile.py" ]]
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
        echo "# $feature_name:" >> $graph_filename
        # echo "  deps: $deps"
        for dep in $deps
        do
            echo "  $feature_name -> $dep" >> $graph_filename
        done
    fi
done
echo -e "\n$(echo $feature_names|xargs)" >> $graph_filename
echo -e "}\n" >> $graph_filename
