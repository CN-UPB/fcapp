#!/bin/bash

# sim normal
for network in "36_mesh" "36_ring" "100_mesh" "100_ring"
do
  for rearr in {0..1}
  do
    echo "Running $network with $rearr ..."
    for seednum in {0..29}
    do
      python csimpfo_fcfs.py "$network" "$rearr" "$seednum" &
    done
    wait
  done
done

# sim BB
for network in "36_mesh" "36_ring"
do
  for BBprob in "0.5"
  do
    for lbb in "0.0" "0.0025" "0.005"
	do
      echo "Running $network with BB_prob $BBprob and L_BB $lbb ..."
      for seednum in {0..29}
      do
        python csimpfo_fcfs_BB.py "$network" "$BBprob" "$lbb" "$seednum" &
      done
      wait
	done
  done
done

# sim CoMP
for network in "36_mesh" "36_ring" "100_mesh" "100_ring"
do
  for rearr in {0..1}
  do
    echo "Running $network with $rearr ..."
    for seednum in {0..29}
    do
      python csimpfo_fcfs_CoMP.py "$network" "$rearr" "$seednum" &
    done
    wait
  done
done

# sim for dist
for network in "36_mesh" "36_ring"
do
  for seednum in {0..29}
  do
    python csimpfo_fcfs_for_dist.py "$network" "$seednum" &
  done
  wait
done

# ES, PS, lessb
for test in "51" "52" "53" "54"
do
  python trun6_fcfs_lessb_bash.py "$test" &
  python trun6_es_lessb_bash.py "$test" &
  python trun6_fcfs_bash.py "$test" &
  python trun6_es_bash.py "$test" &
done
wait

# BB
for test in "51" "52" "53" "54"
do
  for BBprob in "0.5" "1.0"
  do
    for lbb in "0.0" "0.0025" "0.005"
    do
      python trun6_fcfs_BB_bash.py "$test" "$BBprob" "$lbb" &
    done
  done
done
wait

# VCstudy
python trun6_VC_parallel.py 30
wait

# flex for opts
python trun_for_opt_ldf.py
wait
