from __future__ import division
import sys
import math
#from pprint import pprint

import pylab as P

from matplotlib.transforms import Bbox
from matplotlib.font_manager import FontProperties

from collections import defaultdict

from ci import calc_sample_mean

manual_input = False
instances_path = {"ldf": "Results_ldf/ESvsPS", "mdf": "Results/ESvsPS"}
plot_path = "plots_ldf/ESvsPS"
outputlabel = ""
#instances_path = "Results/ESvsPS_lessb"
#plot_path = "plots/ESvsPS_lessb"
#outputlabel = "_lessb"

labels = {}
labels["nodes"] = "Number of nodes" 
labels["flows"] = "Number of DFGs" 
labels["RCAs"] = "Number of RCAs used" 
labels["LCAs"] = "Number of LCAs used" 
labels["Sats"] = "DFGs satisfied (%)" 
labels["rt"] = "Average runtime (s)" 
labels["Flex_es"] = "GreedyFCAPA$_{es}$"
labels["Flex_fcfs"] = "GreedyFCAPA$_{ps}$"
labels["Flex_es_lessb"] = "GreedyFCAPA$_{es}$"
labels["Flex_fcfs_lessb"] = "GreedyFCAPA$_{ps}$"
labels["Flex_es_ldf"] = "GreedyFCAPA$_{es}$ (LDF)"
labels["Flex_fcfs_ldf"] = "GreedyFCAPA$_{ps}$ (LDF)"
labels["Flex_es_mdf"] = "GreedyFCAPA$_{es}$ (MDF)"
labels["Flex_fcfs_mdf"] = "GreedyFCAPA$_{ps}$ (MDF)"

results = {}
xvals = {}
no_nodes = []
topologies = []
Properties = [] 
#Properties = ["Flex_es_lessb","Flex_fcfs_lessb"]
xupper = 6010

inputfiles = []
tests = [51,52,53,54]
obj = ["LCAs","rt","Sats"]
legend_loc = {"LCAs": 'lower right', "rt": 'upper left', "Sats": 'lower left'}

if manual_input:
	for i in xrange(1,len(sys.argv)):
		inputfiles.append(sys.argv[i])
	Properties = []
else:
	for t in tests:
		for p in ["Flex_es","Flex_fcfs"]:
			for k in ["ldf","mdf"]:
				inputfiles.append(instances_path[k] + "\_Results_test_" + str(t) + "_" + p + ".dat")
				
for i in inputfiles:
	fin = open(i, "r")
	tmp = fin.readline().split(" ")
	n = int(tmp[0])
	if not n in no_nodes:
		no_nodes.append(n)
	if not n in results:
		results[n] = {}
		xvals[n] = {}
	t = str(tmp[4])
	if not t in topologies:
		topologies.append(t)
	if not t in results[n]:
		results[n][t] = {}
		xvals[n][t] = []
	no_inst = int(tmp[1])
	flow_mult = int(tmp[2])
	if i[:len(instances_path["ldf"])] == instances_path["ldf"]:
		prop = str(tmp[3]) + "_ldf"
	else:
		prop = str(tmp[3]) + "_mdf"
	if not prop in Properties:
		Properties.append(prop)
	while True:
		tmp = fin.readline().split(" ")
		try:
			if tmp[1] <> "timelimit":
				r = {}
				flows = int(math.ceil(int(tmp[0]) / no_inst) * flow_mult)
				r["flows"] = flows
				if not flows in xvals[n][t]:
					xvals[n][t].append(flows)
				r["prop"] = prop
				r["RCAs"] = float(tmp[1])
				r["LCAs"] = float(tmp[2])
				r["Sats"] = float(tmp[3]) / r["flows"]
				r["rt"] = float(tmp[4])
				r["state"] = str(tmp[5])
				counter = len(results[n][t])
				results[n][t][counter] = r
		except:
			break

#colors = ['#FF0000','#00FF00','#0000FF','#FFFF00','#FF00FF','#00FFFF','#800000','#008000','#000080','#808000','#800080','#008080','#808080','#FFFFFF']
markers = ['^','*','o','v']
font = FontProperties(size=20)
font_smaller = FontProperties(size=16)

for n in no_nodes:
	for t in topologies:
		for p in Properties:
			s = sum(1 for r in results[n][t] if results[n][t][r]["state"] == "Solved" and results[n][t][r]["prop"] == p)
			ns = sum(1 for r in results[n][t] if results[n][t][r]["state"] <> "Solved" and results[n][t][r]["prop"] == p)
			print str(t) + str(n) + ", " + str(p) + ": Solved: " + str(s) + ", Not solved: " + str(ns)	
#exit(1)
	
for n in no_nodes:
	for t in topologies:
		for o in obj:
	
			x_label = "Number of DFGs"
			y_label = labels[o]

			lines = []
			for p in Properties:
				lines.append((n,o,p,t))

			plotdata = {}
			plotconfidence = {}
			xaxis = {}

			xvalues = xvals[n][t]
			xvalues.sort()

			for l in lines:
				print l
				di = []
				ci = []
				xaxis[l] = []
				for x in xvalues:
					values = []
					for r in results[n][t]:
						if x == results[n][t][r]["flows"] and l[2] == results[n][t][r]["prop"]:
							values.append(results[n][t][r][l[1]])
					if len(values) > 20:
						#print l
						#print "ISAMPLES",x,l,len(values)
						#print "IVALUES",x,l,values
						(xd,xc) = calc_sample_mean(values, 0.95)
						xaxis[l].append(x)
						di.append(xd)
						ci.append(xc)
					# else:
						# print "ISAMPLES",x,l,len(values),"!!!"
						# if len(values) > 0:
							# (xd,xc) = (values[0],0)
					
						
				plotdata[l] = di
				plotconfidence[l] = ci
	
			curr_xaxis = xvalues
			#for k in lines:
				#curr_xaxis = sorted(list(set(curr_xaxis).intersection(set(xaxis[k]))))

			#F = P.figure()
			#AX1 = F.add_subplot(111)
			F, AX1 = P.subplots()
			plotlines = []
			plotlabels = []
			for i,l in enumerate(lines):
				#pl = AX1.plot(xaxis, plotdata[l], label=l, lw=2,markersize=12)
				pl = AX1.errorbar(curr_xaxis, plotdata[l][0:len(curr_xaxis)], yerr=plotconfidence[l][0:len(curr_xaxis)], label=(l), lw=2, marker=markers[i], markersize=12, elinewidth=2,ls="--")
				#pl = AX1.errorbar([x for x in xaxis[l]], plotdata[l], yerr=plotconfidence[l], label=(l), lw=2, markersize=12, elinewidth=2, color=colors[i], marker=markers[i],markevery=(i,3))
				plotlines.append(pl[0])
				plotlabels.append(labels[l[2]]) #+ " (" + str(l[0]) + " nodes)")
				#plotlabels.append("Algorithm ({0} GBps/WL)".format(l[0]/1e9))
				#plotlabels.append("Algorithm (d={0} GBps)".format(l[3]/1e9))
				#pl = AX1.errorbar([x for x in xaxis], plotdata[(l,"i")], yerr=plotconfidence[(l,"i")], label=(l,"i"), lw=2, markersize=12, elinewidth=2,ls="--", color=colors[i], marker=markers[i],markevery=(i,3))
				#plotlines.append(pl[0])
				#plotlabels.append((l,"i"))
				#plotlabels.append("ILP Solver ({0} GBps/WL)".format(l[0]/1e9))
				#plotlabels.append("Optimization (d={0} GBps)".format(l[3]/1e9))
			#AX1.hlines([4.515,3.69],-1,21, colors='#606060', linestyles='dotted')
			#AX1.axhline(4.515,color='#606060', linestyle='--',lw=2)
			#AX1.axhline(3.69,color='#606060', linestyle='--',lw=2)
			#AX1.axhline(1.77,color='#606060', linestyle='--',lw=2)
			AX1.set_xlabel(x_label, fontproperties=font)
			AX1.set_ylabel(y_label, fontproperties=font)
			AX1.set_xlim(0, max(curr_xaxis)+10)
			if o == "Sats":
				AX1.set_ylim(0,1.1)
			#elif o == "rt":
				#AX1.set_ylim(0,2)
			#elif o == "LCAs":
				#AX1.set_ylim(0,25)
			#AX1.set_yscale('log')
			for tick in AX1.xaxis.get_major_ticks():
				tick.label1.set_fontsize(16)
			for tick in AX1.yaxis.get_major_ticks():
				tick.label1.set_fontsize(16)
			#AX1.legend()
			#P.legend(plotlines, plotlabels, loc='best', shadow=False, prop=font_smaller, ncol=1)#legend_loc[o]
			P.savefig(plot_path + '/plot_' + l[1] + '_' + l[3] + str(l[0]) + '.pdf', bbox_inches='tight')
			F = P.figure(2)
			F.legend(plotlines, plotlabels, loc='upper left', shadow=False, fancybox=True, prop=font_smaller, ncol=2)
			bb = Bbox.from_bounds(0, 0, 12.8, 3.4)
			P.savefig(plot_path + '/plot_legend' + str(outputlabel) + '.pdf', bbox_inches=bb)
