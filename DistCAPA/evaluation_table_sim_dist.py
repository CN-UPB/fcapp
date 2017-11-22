from __future__ import division
import sys
import math
#from pprint import pprint
import pylab as P
import numpy as np
from matplotlib.transforms import Bbox
from matplotlib.font_manager import FontProperties
from collections import defaultdict
from ci import calc_sample_mean

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
labels["num"] = "Number of reassignments" 

plot_path = "plots/dist_sim"
results_path = "Results"
outputscen = "dist"

results = {}
results_r = {}
topologies = ["36_mesh","36_ring"]
obj = ["#Satisfied","#CLCs","#CLCDiff","#nodeDiff","#flowDiff","CLCpathlength","CLCload","controlRatio","runtime","num"]	
average_obj = ["#Satisfied","#CLCs","#CLCDiff","#nodeDiff","#flowDiff","CLCpathlength","CLCload","controlRatio","runtime"]

for n in topologies:
	results[n] = {}
	for p in range(0,30):
		results[n][p] = {}
		resultsfile = results_path + "/dist_sim/simres_dist_" + str(n) + "_0.5_" + str(p) + ".dat"
		results[n][p]["counter"] = 0
		results[n][p]["flows"] = 0
		results[n][p]["sim"] = {}
		for o in obj:
			results[n][p]["sim"][o] = 0
		
		fin = open(resultsfile, "r")
		tmp = fin.readline()
		
		while True:
			tmp = fin.readline().split(" ")
			try:
				results[n][p]["flows"] += int(tmp[1])
				results[n][p]["sim"]["#Satisfied"] += int(tmp[2]) / int(tmp[1])
				for i in range(1,5):
					results[n][p]["sim"][obj[i]] += int(tmp[i+2])
				for i in range(5,9):
					results[n][p]["sim"][obj[i]] += float(tmp[i+2])
				results[n][p]["sim"]["num"] += 1
				results[n][p]["counter"] += 1
			except:
				break
			
for n in topologies:
	results_r[n] = {}
	for p in range(0,30):
		results_r[n][p] = {}
		resultsfile = results_path + "/flex_for_dist/simres_fcfs_" + str(n) + "_" + str(p) + ".dat"
		results_r[n][p]["counter"] = 0
		results_r[n][p]["flows"] = 0
		results_r[n][p]["sim"] = {}
		for o in obj:
			results_r[n][p]["sim"][o] = 0
		
		fin = open(resultsfile, "r")
		tmp = fin.readline()
		
		while True:
			tmp = fin.readline().split(" ")
			try:
				results_r[n][p]["flows"] += int(tmp[1])
				results_r[n][p]["sim"]["#Satisfied"] += int(tmp[2]) / int(tmp[1])
				for i in range(1,5):
					results_r[n][p]["sim"][obj[i]] += int(tmp[i+2])
				for i in range(5,9):
					results_r[n][p]["sim"][obj[i]] += float(tmp[i+2])
				results_r[n][p]["sim"]["num"] += 1
				results_r[n][p]["counter"] += 1
			except:
				break
				
foutmain = open(plot_path + '/sim_table.dat', "w")

foutmain.write(" & \\multicolumn{2}{|c|}{FlexCAPF} & \\multicolumn{2}{|c|}{DistCAPA} \\\\ \n")
foutmain.write("\\midrule \n")
out = "Network:"	
for i in ["FlexCAPF","DistCAPA"]:		
	for t in topologies:
		out += " & " + str(t[-4:]+t[:-5])
foutmain.write(out + "\\\\ \n")
foutmain.write("\\midrule \n")
out = "Reassignments:"	
for n in topologies:
	out += " & " + str(round(sum(results_r[n][p]["counter"] for p in range(0,30))/30,2)) 			
for n in topologies:
	out += " & " + str(round(sum(results[n][p]["counter"] for p in range(0,30))/30,2)) 
foutmain.write(out + "\\\\ \n")
out = "LCA reassignments:"	
for n in topologies:
	out += " & " + str(round(sum(results_r[n][p]["sim"]["#CLCDiff"] for p in range(0,30))/30,2))			
for n in topologies:
	out += " & " + str(round(sum(results[n][p]["sim"]["#CLCDiff"] for p in range(0,30))/30,2))
foutmain.write(out + "\\\\ \n")	
out = "Node reassignments:"				
for n in topologies:
	out += " & " + str(round(sum(results_r[n][p]["sim"]["#nodeDiff"] for p in range(0,30))/30,2))			
for n in topologies:
	out += " & " + str(round(sum(results[n][p]["sim"]["#nodeDiff"] for p in range(0,30))/30,2))
foutmain.write(out + "\\\\ \n")
out = "DFG reassignments:"				
for n in topologies:
	out += " & " + str(round(sum(results_r[n][p]["sim"]["#flowDiff"] for p in range(0,30))/30,2))			
for n in topologies:
	out += " & " + str(round(sum(results[n][p]["sim"]["#flowDiff"] for p in range(0,30))/30,2))
foutmain.write(out + "\\\\ \n")

foutmain.close()