from __future__ import division
import sys
import math
#from pprint import pprint

#import pylab as P

#from matplotlib.transforms import Bbox
#from matplotlib.font_manager import FontProperties

from collections import defaultdict

from ci import calc_sample_mean

manual_input = False

labels = {}
labels["nodes"] = "Number of nodes" 
labels["flows"] = "Number of flows" 
labels["CRCs"] = "Number of CRCs used" 
labels["CLCs"] = "Number of CLCs used" 
labels["Sats"] = "Flows satisfied (%)" 
labels["rt"] = "Average runtime (s)"
labels["ilp"] = "FCPF MIQCP"
labels["greedy"] = "FCPF greedy heuristic"
labels["ga"] = "FCPF genetic algorithm"

results = []
no_nodes = []
Properties = ["ilp","greedy"]
obj = ["CLCs","rt"]#,"Sats","CRCs"]		

inputfiles = []
tests = [19,20]

if manual_input:
	for i in xrange(1,len(sys.argv)):
		inputfiles.append(sys.argv[i])
	Properties = []
else:
	for t in tests:
		for p in Properties:
			inputfiles.append("Instances\_Results_test_" + str(t) + "_" + p + ".dat")

for i in inputfiles:
	fin = open(i, "r")
	tmp = fin.readline().split(" ")
	n = int(tmp[0])
	if not n in no_nodes:
		no_nodes.append(n)
	no_inst = int(tmp[1])
	flow_mult = int(tmp[2])
	prop = tmp[3]
	if not prop in Properties:
		Properties.append(prop)
	while True:
		tmp = fin.readline().split(" ")
		try:
			if tmp[1] != "timelimit":
				r = {}
				r["nodes"] = n
				r["flows"] = int(math.ceil(int(tmp[0]) / no_inst) * flow_mult)
				r["prop"] = prop
				r["CRCs"] = float(tmp[1])
				r["CLCs"] = float(tmp[2])
				r["Sats"] = float(tmp[3]) / r["flows"]
				r["rt"] = float(tmp[4])
				results.append(r)
		except:
			break

for o in obj:
			
	x_label = "Number of data flows"
	y_label = labels[o]

	lines = []
	for n in no_nodes:
		for p in Properties:
			lines.append((n,o,p))

	plotdata = {}
	plotconfidence = {}
	xaxis = {}

	xvalues = range(1,210)

	for l in lines:
		di = []
		ci = []
		xaxis[l] = []
		for x in xvalues:
			values = []
			for r in results:
				if l[0] == r["nodes"] and x == r["flows"] and l[2] == r["prop"]:
					values.append(r[l[1]])
			if len(values) > 50:
				print "ISAMPLES",x,l,len(values)
				print "IVALUES",x,l,values
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

	#colors = ['#FF0000','#00FF00','#0000FF','#FFFF00','#FF00FF','#00FFFF','#800000','#008000','#000080','#808000','#800080','#008080','#808080','#FFFFFF']
	markers = ['^','*','o','v']

	font = FontProperties(size=24)
	font_smaller = FontProperties(size=18)
	
	for n in no_nodes:
		curr_lines = []
		for l in lines:
			if l[0] == n:
				curr_lines.append(l)
		
		curr_xaxis = range(1,500)
		for k in curr_lines:
			curr_xaxis = sorted(list(set(curr_xaxis).intersection(set(xaxis[k]))))

		F = P.figure()
		AX1 = F.add_subplot(111)
		plotlines = []
		plotlabels = []
		for i,l in enumerate(curr_lines):
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
		if l[1] == "rt":
			AX1.set_yscale('log')
		for tick in AX1.xaxis.get_major_ticks():
			tick.label1.set_fontsize(24)
		for tick in AX1.yaxis.get_major_ticks():
			tick.label1.set_fontsize(24)
		#AX1.legend()
		P.savefig('plots/plot_' + l[1] + '_' + str(l[0]) + '_nodes.pdf', bbox_inches='tight')
		F = P.figure(2)
		F.legend(plotlines, plotlabels, loc='upper left', shadow=False, fancybox=True, prop=font_smaller, ncol=2)
		#bb = Bbox.from_bounds(0, 0, 12.8, 1.8)
		#bb = Bbox.from_bounds(0, 0, 6.4, 3.4)
		bb = Bbox.from_bounds(0, 0, 6.4, 4)
		P.savefig('plots/plot_legend.pdf', bbox_inches=bb)
