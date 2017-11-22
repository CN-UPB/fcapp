# FCAPP testbed (with FlexCAPF proof-of-concept implementation)

Required: Python 2.7 + Python packages: networkx, numpy and matplotlib + see appendix_doku.pdf

- appendix_doku.pdf contains the appendix of the master thesis during whose course the testbed was created and contains several information about setting up the testbed environment and executing emulation experiments.
- cp_flex_fcfs.py is the FlexCAPF proof-of-concept implementation (which uses crowd_network.py)
- csimpfo_fcfs.py steers emulation experiments (e.g. includes the non-stationary Poisson process for DFG request generation)
- fcapf_ryu_controller.py is the FCAPP Ryu SDN controller
- flowtypes_new.csv and flowtypes_CoMP.csv contain the description of the generic/CoMP DFG scenarios (used by crowd_network.py)
- Network_36_mesh.dat and Network_36_ring.dat are topology description files that can be used for emulation experiments 
- results.rar contains the results generated for the testbed chapter in my PhD thesis (Network_36_mesh.dat with generic/CoMP DFG scenarios)
- make_plots.bat, plotlcaused.py and runtimeplot.py were used for generation the plots for the aforementioned chapter
- MaxiNet.cfg is an example MaxiNet configuration file
- cleanfront.sh and cleanworker.sh are scripts to clean up the MaxiNet frontend/workers
- iperf2-code contains the modified Iperf used in the testbed