#!/bin/bash

dim1=6
dim2=6
for i in {0..29}
do
  for j in {0..49}
  do
    flows=$(( 100 * $i + 100 ))
    buff=`echo "python Generator_mesh8.py "$dim1" "$dim2" "$flows" ba-networks/"$dim1"-"$flows"-"$j""`
    $buff
  done
done

