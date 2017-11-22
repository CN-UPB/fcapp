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
labels["Flex_fcfs"] = "FlexCAPF ($P_{BB} = 0.0$)"

plot_path = "plots_ldf/sim_BB"
results_path = "Results_ldf/sim"
results_path_BB = "Results_ldf/sim_BB"
outputscen = "fcfs_BB"

results = {}
Properties = ["Flex_fcfs"] 
for bbprob in [0.5]:
	for lbb in [0.0,2.5,5.0]:
		prop = "Flex_fcfs_BB_" + str(bbprob) + "_" + str(lbb)
		Properties.append(prop)
		labels[prop] = "FlexCAPF ($P_{BB}$ = " + str(bbprob) + ", $l_{BB}$ = " + str(lbb) + "ms)"
topologies = ["36_mesh","36_ring"]#,"100_mesh","100_ring"]
obj = ["#Satisfied","#CRCs","#CLCs","#CLCDiff","#nodeDiff","#flowDiff","CRCpathlength","CLCpathlength","CLCload","controlRatio","runtime"]	

for t in topologies:
	results[t] = {}
	for prop in Properties:
		results[t][prop] = {}
		for s in range(0,30):
			results[t][prop][s] = {}
			if prop == "Flex_fcfs":
				resultsfile = results_path + "\simres_fcfs_" + str(t) + "_False_" + str(s) + ".dat"
			else:
				resultsfile = results_path_BB + "\simres_fcfs_BB_" + str(t) + "_" + prop[-7:] + "_" + str(s) + ".dat"
			results[t][prop][s]["counter"] = 0
			results[t][prop][s]["flows"] = 0
			results[t][prop][s]["sim"] = {}
			results[t][prop][s]["scratch"] = {}
			for o in obj:
				results[t][prop][s]["sim"][o] = 0
				results[t][prop][s]["scratch"][o] = 0
			
			fin = open(resultsfile, "r")
			tmp = fin.readline()
			
			while True:
				tmp = fin.readline().split(" ")
				try:
					results[t][prop][s]["flows"] += int(tmp[1])
					for i in range(0,6):
						results[t][prop][s]["sim"][obj[i]] += int(tmp[i+2])
						results[t][prop][s]["scratch"][obj[i]] += int(tmp[i+2+len(obj)])
					for i in range(6,len(obj)):
						results[t][prop][s]["sim"][obj[i]] += float(tmp[i+2])
						results[t][prop][s]["scratch"][obj[i]] += float(tmp[i+2+len(obj)])
					results[t][prop][s]["counter"] += 1
				except:
					break
				
for t in topologies:
	for prop in Properties:
		for s in range(0,30):
			results[t][prop][s]["flows"] /= results[t][prop][s]["counter"]
			for o in obj:
				results[t][prop][s]["sim"][o] /= results[t][prop][s]["counter"]
				results[t][prop][s]["scratch"][o] /= results[t][prop][s]["counter"]

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
	width = 0.1
	AX1.set_xticks(ind+width*0.5*(2*len(Properties)-1))
	AX1.set_xticklabels([t[-4:]+t[:-5] for t in topologies])
	
	ysim = {}
	yscratch = {}
	ysim_err = {}
	yscratch_err = {}

	for prop in Properties:
		ysim[prop] = []
		yscratch[prop] = []
		ysim_err[prop] = []
		yscratch_err[prop] = []
		for t in topologies:
			values = [results[t][prop][s]["sim"][o] for s in range(0,30)]
			(xd,xc) = calc_sample_mean(values, 0.95)
			ysim[prop].append(xd)
			ysim_err[prop].append(xc)
			values = [results[t][prop][s]["scratch"][o] for s in range(0,30)]
			(xd,xc) = calc_sample_mean(values, 0.95)
			yscratch[prop].append(xd)
			yscratch_err[prop].append(xc)
		
	plotlabels = []
	plotlines = []
	
	i = 0
	for prop in Properties:
		pl = AX1.bar(ind+i*width, ysim[prop], width, yerr=ysim_err[prop], capsize=6)
		plotlines.append(pl[0])
		plotlabels.append(labels[prop])
		i += 1
	for prop in Properties:
		pls = AX1.bar(ind+i*width, yscratch[prop], width, hatch='//', yerr=yscratch_err[prop], capsize=6, color=plotlines[i-len(Properties)].get_facecolor())
		#plotlines.append(pls[0])
		#plotlabels.append(labels[prop] + " Scratch comparison")
		i += 1
	
	AX1.set_ylim(ymin=0)
	#AX1.set_yscale('log')
	for tick in AX1.xaxis.get_major_ticks():
		tick.label1.set_fontsize(18)
	for tick in AX1.yaxis.get_major_ticks():
		tick.label1.set_fontsize(18)
	P.savefig(plot_path + '/plot_' + str(outputscen) + '_' + str(o).replace("#","") + '.pdf', bbox_inches='tight')
	
	pls = AX1.bar(ind+i*width, yscratch[prop], width, hatch='//', yerr=yscratch_err[prop], capsize=6, color='white')
	plotlines.append(pls[0])
	plotlabels.append("Corresponding scratch comparisons")
	
	F = P.figure()
	F.legend(plotlines, plotlabels, loc='upper left', shadow=False, fancybox=True, prop=font_smaller)
	#bb = Bbox.from_bounds(0, 0, 6.4, 4)
	P.savefig(plot_path + '/plot_legend_1_col.pdf', bbox_inches='tight')
	#F = P.figure()
	#F.legend(plotlines, plotlabels, loc='upper left', shadow=False, fancybox=True, prop=font_smaller, ncol=2)
	#bb = Bbox.from_bounds(0, 0, 7, 2)
	#P.savefig(plot_path + '/plot_legend_2_col.pdf', bbox_inches='tight')
			
		
