# FCAPP Genetic algorithms

Comment: The FCAPP Genetic Algorithms use the inferior equal-share processing model

Required: Python 2.7 + Python packages: networkx, numpy and matplotlib

- BashG_GA.sh, Generator_mesh8.py, flowtypes_new.csv and ChModel.py are used to generate test networks
- results_GA.tar.gz contains all result files used in the GA chapter of my PhD thesis
- networks_GA.tar.gz (all corresponding test networks) is too big for Github and can be found at https://drive.google.com/file/d/15_AgOeqAdbr5W41G_NWRx-W8nImh4gRi/view?usp=sharing
- ba-code/ contains all program code and scripts 

Within ba-code/, evaluation plots of the results can be created using the "eval_mod.py" file (see bottom of that file for details how to create those plots).
Program runs are performed using maina.py and the trun_GA_parallel.py script.
 - maina.py is for doing a single run for a single setting for just one network.
 - trun_GA_parallel.py can be used to launch an custom amount of runs with specified settings in parallel on multiple CPUs
 
===========================================================
possible configurations in the configuration string:
-----------------------------------------------------------
flowOrder: leastDemanding, mostDemanding or random    (the flow ordering scheme)
useHopPathLength: 0 or 1   (1 -> use path length with hops, 0 -> use path latency)
mu: e.g. 20   (population size)
cxpb: e.g. 0.2    (crossover probability)
survivorSelection: best or tournament   (survivor selection scheme)
tsize: e.g. 2    (tournament size)
vcFactor: e.g. 5.0    (beta - see thesis)
dim: e.g. 6      (the graph will have 6x6 nodes, requires generating the corresponding test networks first)
numFlows: e.g. 1000    (the number of flows to be used, requires generating the corresponding test networks first)
bFlowFactor: 1.0 or 20.0     (factor for data rate required by DFGs)
fitness4th: none, min or mean    (how to define the fourth fitness component)
representation: greedy, ga1, ga2, ga2b, ga3 or ga3b    (the algorithm to be used - the b versions are the variants)

SYNTAX for configuration string: "key=value,key2=value2,...".

Comment: All filenames and folder strucutres were adopted from the bachelor thesis the GA approaches initially originated from.