from __future__ import division
import time

from fcpf_greedy import *


filename = '../../res/cpp/tf4-1000-5.dat'
#filename = '../../res/cpp/l10-2500.dat'

print("Running greedy algorithm on '{}'".format(filename))
cpg = CPGreedy(filename, modify_controllers=True, contrProb=.5)

tstart = time.time()
cpg.cpgreedy()
tend = time.time()

print("State: " + cpg.state)
if cpg.state == "NOT SOLVED":
	print("Remaining nodes: " + str([i for i in cpg.cn.V if not i in cpg.Controlled]))
print("CRCs: " + str(len(cpg.CRCs)) )
print(str(cpg.CRCs))
print("CLCs: " + str(len(cpg.CLCs)) + " (out of " + str(len(cpg.cn.C)) + " available)")
print(str(cpg.CLCs))
print("Flows satisfied: " + str(len(cpg.Satisfied)) + " out of " + str(len(cpg.cn.F)))
print("Runtime: " + str(tend - tstart) + " seconds")

#cpg.cn.output(legend=False)