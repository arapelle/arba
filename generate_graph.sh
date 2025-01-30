#!/usr/bin/env bash

graph_fpath="/tmp/arba.gv"
svg_fpath="arba.svg"

echo "# To generate svg: dot -Tsvg graph.gv > graph.svg

digraph G
{
#  rankdir = LR;
  graph [fontname = \"helvetica\"];
  node [style=radial, fillcolor=\"white:lightgreen\"];
  node [fontname=\"monospace\"; fontsize=13];
  edge [fontname=\"helvetica\"];
  label = arba;
" > $graph_fpath

projects=`find -maxdepth 1 -name "arba-????"|sort`
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
        echo "# $feature_name:" >> $graph_fpath
        # echo "  deps: $deps"
        for dep in $deps
        do
            echo "  $feature_name -> $dep" >> $graph_fpath
        done
    fi
done
echo -e "\n$(echo $feature_names|xargs)" >> $graph_fpath
echo -e "}\n" >> $graph_fpath

dot -Tsvg $graph_fpath > $svg_fpath
