#!/bin/bash

for network in "36_mesh" "36_ring" 
do
  for LLlimit in "0.5"
  do
    echo "Running $network with $LLlimit ..."
    for seednum in {0..29}
    do
      python csimpfo_greedyFL.py "$network" "$LLlimit" "$seednum" &
    done
    wait
  done
done
