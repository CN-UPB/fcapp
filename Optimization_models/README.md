# FCAPP Optimization models

Required: Gurobi, Python 2.7 + Python packages: Pyomo, networkx

- cp_crowd_es.py is the Pyomo-based implementation of the FCAPP equal-share optimization model
- cp_crowd_fcfs.py is the Pyomo-based implementation of the FCAPP proportional-share optimization model
- cp_crowd_fcfs_BB.py is the Pyomo-based implementation of the FCAPP proportional-share optimization model with backbone extension
- crun_es_single.py, crun_fcfs_single.py and crun_fcfs_BB_single.py can be used to execute single instances of the optimization models
- trun_opt_parallel.py can be used to enqueue severel optimization runs for a certain number of CPUs in parallel
- Generator_mesh8_mega.py and Generator_mesh8_mega_CoMP.py can be used to create new test networks with Genereic and CoMP DFGs respectively (both use ChModel.py)
- flowtypes_new.csv and flowtypes_CoMP.csv contain the description of the generic/CoMP DFG scenarios (used by the topology generation scripts)
- evaluation_plot.py is a script used to generate plots (uses ci.py)
- results_opt.rar includes all result files for optimization models used in my Phd thesis
- networks_opt.rar (all corresponding test networks) is too big for Github and can be found at https://drive.google.com/file/d/1u9CUhjlRnvVxig002yog-XHIb4DkeD-Y/view?usp=sharing