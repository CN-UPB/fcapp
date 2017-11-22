# FCAPP Greedy-based heuristic algorithms/frameworks
# (all versions of FlexCAPF and GreedyFCAPA) 

Required: Python 2.7 + Python packages: networkx, numpy, matplotlib

- cp_flex_fcfs.py is the FlexCAPF version with proportional-share scheduling. It also includes GreedyFCAPA (flexOperation=False) and the FlexCAPF backbone extension (considerBBconnections=True)
- cp_flex_es.py is the FlexCAPF version with equal-share scheduling. It also includes GreedyFCAPA (flexOperation=False)
- crowd_network.py stores the simulated networks and is needed by the aforementioned files
- csimpfo_*.py steer simulation runs (e.g. includes the non-stationary Poisson process for DFG request generation), require seeds.py
- trun_all.sh, trun6_*.py are scripts used for statis placement evaluation runs
- Generator_mesh8.py and Generator_ring2.py can be used to create new test networks with mesh and ring topology respectively (both use ChModel.py)
- flowtypes_new.csv and flowtypes_CoMP.csv contain the description of the generic/CoMP DFG scenarios (used by several other files)
- evaluation_*.py are scripts used to generate plots/tables (partially use ci.py)
- Instances.rar includes all test networks used for the Greedy-based heuristics in my Phd thesis
- results.rar includes all results for the Greedy-based heuristics in my Phd thesis