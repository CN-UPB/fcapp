# Distributed flow processing-aware Control Application Placement Algorithm (DistCAPA)

Required: Python 2.7 + Python packages: networkx, numpy and matplotlib, simpy 2.2 (simpy-2.2.zip), ComplexNetworkSim 0.1.2 (ComplexNetworkSim-0.1.2.zip)

- networks.rar contains all networks used in the DistCAPA chapter of my PhD thesis
- results.rar contains all results used in the DistCAPA chapter of my PhD thesis
- GreedyFL_Flows.py contains the DistCAPA algorithm
- Simulation_GreedyFL.py is used to execute DistCAPA (requires GreedyFL_Flows.py, lib/ folder and Manager.py)
- csimpfo_greedyFL.py steers simulation runs (e.g. includes the non-stationary Poisson process for DFG request generation), requires Simulation_GreedyFL.py and seeds.py
- simrun_dist.sh can be used to start multiple simulation runs in parallel
- trun_GreedyFL_parallel.py can be used to perform multiple initial placement runs in parallel (requires trun_GreedyFL_single.py)
- flowtypes_new.csv contains the description of the generic DFG scenario (used by lib/crowd_network.py)
- evaluation_plot_dist.py, evaluation_plot_sim_dist.py, evaluation_table_sim_dist.py and ci.py can be used to produce plots/tables from result files