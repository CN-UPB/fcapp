from __future__ import division
import sys
import math
#from pprint import pprint
import pylab as P
import numpy as np
from matplotlib.transforms import Bbox
from matplotlib.font_manager import FontProperties
from collections import defaultdict

labels = {}
labels["nodes"] = "Number of nodes" 
labels["#flows"] = "Number of DFGs" 
labels["#Satisfied"] = "DFGs satisfied (%)" 
labels["#CRCs"] = "Number of RCAs used" 
labels["#CLCs"] = "Number of LCAs used" 
labels["#CLCDiff"] = "Number of new LCAs" 
labels["#nodeDiff"] = "New node assignments" 
labels["#flowDiff"] = "New DFG assignments" 
labels["CRCpathlength"] = "Average RCA path length" 
labels["CLCpathlength"] = "Average LCA path length" 
labels["CLCload"] = "Average LCA load" 
labels["controlRatio"] = "LCA control ratio" 
labels["runtime"] = "runtime (s)" 

plot_path = "plots_ldf/sim_CoMP"
results_path = "Results_ldf/sim_CoMP_0.8"
outputscen = "CoMP_0.8"

results = {}
topologies = ["36_mesh","36_ring","100_mesh","100_ring"]
obj = ["#Satisfied","#CRCs","#CLCs","#CLCDiff","#nodeDiff","#flowDiff","CRCpathlength","CLCpathlength","CLCload","controlRatio","runtime"]		

for n in topologies:
	results[n] = {}
	for p in range(0,30):
		results[n][p] = {}
		resultsfile = results_path + "\simres_fcfs_" + str(n) + "_False_" + str(p) + ".dat"
		results[n][p]["counter"] = 0
		results[n][p]["flows"] = 0
		results[n][p]["lastCLCs"] = 0
		results[n][p]["HLcounter"] = 0
		results[n][p]["LLcounter"] = 0
		results[n][p]["HLrt"] = 0
		results[n][p]["LLrt"] = 0
		results[n][p]["sim"] = {}
		results[n][p]["scratch"] = {}
		for o in obj:
			results[n][p]["sim"][o] = 0
			results[n][p]["scratch"][o] = 0
		
		fin = open(resultsfile, "r")
		tmp = fin.readline()
		
		while True:
			tmp = fin.readline().split(" ")
			try:
				results[n][p]["flows"] += int(tmp[1])
				for i in range(0,6):
					results[n][p]["sim"][obj[i]] += int(tmp[i+2])
					results[n][p]["scratch"][obj[i]] += int(tmp[i+2+len(obj)])
				for i in range(6,len(obj)):
					results[n][p]["sim"][obj[i]] += float(tmp[i+2])
					results[n][p]["scratch"][obj[i]] += float(tmp[i+2+len(obj)])
				results[n][p]["counter"] += 1
				if int(tmp[4]) > results[n][p]["lastCLCs"]:
					results[n][p]["HLcounter"] += 1
					results[n][p]["HLrt"] += float(tmp[12])
				else: 
					results[n][p]["LLcounter"] += 1
					results[n][p]["LLrt"] += float(tmp[12])
				results[n][p]["lastCLCs"] = int(tmp[4])
			except:
				break

foutmain = open(plot_path + '/' + outputscen + '_rt_table.dat', "w")

out = "Network:"				
for t in topologies:
	out += " & " + str(t[-4:]+t[:-5])
foutmain.write(out + "\\\\ \n")
foutmain.write("\\midrule \n")
# out = "Average number of DFGs:"				
# for n in topologies:
	# out += " & " + str(int(sum(results[n][p]["flows"]/results[n][p]["counter"] for p in range(0,30))/30))
# foutmain.write(out + "\\\\ \n")	
out = "Average number of runs (total):"				
for n in topologies:
	out += " & " + str(round(sum(results[n][p]["counter"] for p in range(0,30))/30,2)) 
foutmain.write(out + "\\\\ \n")
out = "Average number of runs (HL):"				
for n in topologies:
	out += " & " + str(round(sum(results[n][p]["HLcounter"] for p in range(0,30))/30,2)) 
foutmain.write(out + "\\\\ \n")
out = "Average number of runs (LL):"				
for n in topologies:
	out += " & " + str(round(sum(results[n][p]["LLcounter"] for p in range(0,30))/30,2)) 
foutmain.write(out + "\\\\ \n")
out = "Average runtime (reass.):"				
for n in topologies:
	out += " & " + str(round(sum(results[n][p]["sim"]["runtime"] / results[n][p]["counter"] for p in range(0,30))/30,3)) + " s"
foutmain.write(out + "\\\\ \n")	
out = "Average runtime (HL):"				
for n in topologies:
	out += " & " + str(round(sum(results[n][p]["HLrt"]/results[n][p]["HLcounter"] for p in range(0,30))/30,3)) + " s"
foutmain.write(out + "\\\\ \n")	
out = "Average runtime (LL):"				
for n in topologies:
	out += " & " + str(round(sum(results[n][p]["LLrt"]/results[n][p]["LLcounter"] for p in range(0,30))/30,3)) + " s"
foutmain.write(out + "\\\\ \n")		
out = "Average runtime (scratch):"				
for n in topologies:
	out += " & " + str(round(sum(results[n][p]["scratch"]["runtime"] / results[n][p]["counter"] for p in range(0,30))/30,3)) + " s"
foutmain.write(out + "\\\\ \n")	

foutmain.close()
