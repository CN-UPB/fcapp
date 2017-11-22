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
labels["#CLCDiff"] = "Number of changed LCAs" 
labels["#nodeDiff"] = "New node assignments" 
labels["#flowDiff"] = "New DFG assignments" 
labels["CRCpathlength"] = "Average RCA path length" 
labels["CLCpathlength"] = "Average LCA path length" 
labels["CLCload"] = "Average LCA load" 
labels["controlRatio"] = "LCA control ratio" 
labels["runtime"] = "runtime (s)" 

plot_path = "plots_ldf/sim"
results_path = "Results_ldf/sim"
outputscen = "fcfs"

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
			except:
				break
				
for n in topologies:
	for p in range(0,30):
		results[n][p]["flows"] /= results[n][p]["counter"]
		for o in obj:
			results[n][p]["sim"][o] /= results[n][p]["counter"]
			results[n][p]["scratch"][o] /= results[n][p]["counter"]

markers = ['^','*','o','v']
font_bigger = FontProperties(size=28)
font_smaller = FontProperties(size=18)
			
for o in obj:
	print "Creating graph for " + str(o)
	y_label = labels[o]
	F = P.figure()
	AX1 = F.add_subplot(111)
	AX1.set_ylabel(y_label, fontproperties=font_smaller)
	ind = np.arange(len(topologies))
	width = 0.35
	AX1.set_xticks(ind+width/2)
	AX1.set_xticklabels([t[-4:]+t[:-5] for t in topologies])
	
	ysim = []
	yscratch = []
	ysim_err = []
	yscratch_err = []

	for n in topologies:
		values = [results[n][p]["sim"][o] for p in range(0,30)]
		(xd,xc) = calc_sample_mean(values, 0.95)
		ysim.append(xd)
		ysim_err.append(xc)
		values = [results[n][p]["scratch"][o] for p in range(0,30)]
		(xd,xc) = calc_sample_mean(values, 0.95)
		yscratch.append(xd)
		yscratch_err.append(xc)
		
	plotlabels = []
	plotlines = []
			
	pl = AX1.bar(ind, ysim, width, color='blue', yerr=ysim_err, capsize=10)
	plotlines.append(pl[0])
	plotlabels.append("Reassignment")
	pls = AX1.bar(ind+width, yscratch, width, color='red', yerr=yscratch_err, capsize=10)
	plotlines.append(pls[0])
	plotlabels.append("Scratch comparison")
	
	AX1.set_ylim(ymin=0)
	#AX1.set_yscale('log')
	for tick in AX1.xaxis.get_major_ticks():
		tick.label1.set_fontsize(18)
	for tick in AX1.yaxis.get_major_ticks():
		tick.label1.set_fontsize(18)
	P.savefig(plot_path + '/plot_' + str(outputscen) + '_' + str(o).replace("#","") + '.pdf', bbox_inches='tight')
	F = P.figure()
	F.legend(plotlines, plotlabels, loc='upper left', shadow=False, fancybox=True, prop=font_smaller)
	#bb = Bbox.from_bounds(0, 0, 6.4, 4)
	P.savefig(plot_path + '/plot_legend_1_col.pdf', bbox_inches='tight')
	F = P.figure()
	F.legend(plotlines, plotlabels, loc='upper left', shadow=False, fancybox=True, prop=font_smaller, ncol=2)
	#bb = Bbox.from_bounds(0, 0, 7, 2)
	P.savefig(plot_path + '/plot_legend_2_col.pdf', bbox_inches='tight')
			
		
