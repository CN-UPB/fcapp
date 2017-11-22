# coding=utf-8
from __future__ import (absolute_import, division, print_function)
from collections import defaultdict
import os
import re
import math
import numpy as np
from existing_code import ci
from mycode import utilf
import util
from mycode import evalplt

class RunData(object):
	def __init__(self, proc_id, dt, fitness_values, fitness_score, c_usage):
		self.proc_id = proc_id
		self.dt = dt
		self.fitness_values = fitness_values
		self.fitness_score = fitness_score
		self.c_usage = c_usage

	def __str__(self):
		return "{},{},{}".format(self.dt, self.fitness_values, self.fitness_score)

	@staticmethod
	def create_by_line(line):
		ire = "\d+"
		fre = "[-+]?\d*\.\d+|\d+"
		sre = "#({1}): dt: ({0}), fit: \\(({0}),({0}),({0}),({0})\\),({0}), ind: .*Used controllers: ({1}) / ({1})".format(fre, ire)
		try:
			result = re.findall(sre, line)[0]
			return RunData(proc_id=int(result[0]), dt=float(result[1]), fitness_values=tuple(map(float, result[2:6])),
					   fitness_score=float(result[6]), c_usage=(float(result[7]) / float(result[8])))
		except Exception, err:
			#print(err)
			return None

class FileData(object):

	ASSERT48 = True

	def __init__(self, filename):
		fin = open(filename, "r")
		first_line = fin.readline()
		if first_line.endswith("\n"):
			first_line = first_line[:-1]
		self.settings = util.get_user_settings(first_line[10:])
		self.run_datas = []
		for line in fin:
			rd = RunData.create_by_line(line)
			if rd is not None:
				self.run_datas.append(rd)
		self.run_datas.sort(key=lambda it: it.proc_id)
		assert len(self.run_datas) > 0, "no data"
		if FileData.ASSERT48:
			assert len(self.run_datas) == 50, "wrong number of data points"

	def merge_with(self, fd):
		assert self.settings == fd.settings
		self.run_datas.extend(fd.run_datas)

	def __str__(self):
		return "{},{}\navg dt, fscore: {}, {}".format(self.settings,[str(it) for it in self.run_datas],
													  utilf.mean(self.performances), utilf.mean(self.fitness_scores))

	def get_setting(self, name):
		return self.settings[name] if name in self.settings else util.DEFAULT_DIC[name]

	def get_key(self, xattr_name):
		kdic = dict(self.settings)
		if xattr_name not in kdic:
			kdic[xattr_name] = util.DEFAULT_DIC[xattr_name]
		return tuple(sorted(kdic.items()))

	@property
	def performances(self):
		return [it.dt for it in self.run_datas]

	@property
	def fitness_values(self):
		return [it.fitness_values for it in self.run_datas]

	@property
	def num_controllers(self):
		return [it.fitness_values[2] for it in self.run_datas]

	@property
	def used_controller_percentages(self):
		return [100.0 * float(it.c_usage) for it in self.run_datas]

	@property
	def num_unsatisfied_flows(self):
		return [it.fitness_values[1] for it in self.run_datas]

	@property
	def fitness_scores(self):
		return [it.fitness_score for it in self.run_datas]
		
	@property
	def num_LCAs(self):
		return [it.fitness_values[2]-1 for it in self.run_datas]

def get_file_path(base_dir, filename):
	if not base_dir.endswith("/"):
		base_dir += "/"
	return base_dir + filename

class DirData(object):
	def __init__(self, dir_path, xattr_name):
		file_datas = dict()
		for filename in sorted(os.listdir(dir_path)):
			if filename.endswith(".dat"):
				try:
					fd = FileData(get_file_path(dir_path, filename))
					key = fd.get_key(xattr_name)
					if key in file_datas:
						#assert False, "config exists"
						#file_datas[key].merge_with(fd)
						file_datas[key] = fd

					else:
						file_datas[key] = fd
				except Exception, err:
					print("Failed to parse file: '{}'".format(filename))
					print(err.message)
		self.fds = list(sorted(file_datas.values(), key=lambda it: tuple(sorted(it.settings.items()))))

	def __str__(self):
		s = ""
		return s

class Subgroup(object):

	XAXIS_BOUNDS = 0, 1000

	def __init__(self, fdlist_new, fdlist_old, label, xaxis_attr, yuse):
		self.fdlist_new = fdlist_new
		self.fdlist_old = fdlist_old
		self.label = label
		self.xaxis_attr = xaxis_attr
		self.yuse = yuse
		self._sort(self.fdlist_new)
		if fdlist_old is not None:
			self._sort(self.fdlist_old)

	def _in_bounds(self, val):
		return Subgroup.XAXIS_BOUNDS[1] >= val >= Subgroup.XAXIS_BOUNDS[0]

	def _sort(self, fdlist):
		fdlist.sort(key=lambda it: it.settings[self.xaxis_attr] if self.xaxis_attr in it.settings else util.DEFAULT_DIC[self.xaxis_attr])
		fdlist[:] = [it for it in fdlist if self._in_bounds(it.get_setting(self.xaxis_attr))]

	def _get_y_values(self, file_data):
		if self.yuse == 0:
			return file_data.performances
		elif self.yuse == 5:
			return file_data.fitness_scores
		elif self.yuse == 3:
			#return file_data.num_controllers
			return file_data.num_LCAs
		elif self.yuse == 2:
			return file_data.num_unsatisfied_flows
		elif self.yuse == 6:
			return file_data.used_controller_percentages
		else:
			assert False

	def create_line(self):
		def get_percentage(new_val, old_val):
			if old_val == 0:
				return 100.0
			return 100.0 * new_val / old_val
		line = evalplt.Line()
		line.label = "<todo>" + self.label
		for i in xrange(len(self.fdlist_new)):
			fd_new = self.fdlist_new[i]
			if self.fdlist_old is not None:
				fd_old = None
				for fd in self.fdlist_old:
					if fd.get_setting(self.xaxis_attr) == fd_new.get_setting(self.xaxis_attr):
						fd_old = fd
				if fd_old is None:
					continue
				assert fd_new.get_setting(self.xaxis_attr) == fd_old.get_setting(self.xaxis_attr)
				yvalues_new, yvalues_old = self._get_y_values(fd_new), self._get_y_values(fd_old)
				yvalues = [get_percentage(new_val, old_val) for new_val, old_val in zip(yvalues_new, yvalues_old)]
			else:
				yvalues = self._get_y_values(fd_new)
			mean, cihl = ci.calc_sample_mean(yvalues, p=.95)
			line.xs.append(fd_new.get_setting(self.xaxis_attr))
			line.ys.append(mean)
			line.yerrs.append(cihl)
			line.label = self.label
		return line

def _get_fdlist_for_filter_in_dir_data(dd, config_filter, xattr):
	config_dic = util.get_user_settings(config_filter, xattr=xattr)
	fdlist = []
	for fd in dd.fds:
		if set(fd.settings.keys()) - set(config_dic.keys()) <= {xattr} and (
						set(config_dic.keys()) <= set(fd.settings.keys()) and
					all(config_dic[it] == fd.settings[it] for it in config_dic)
		):
			fdlist.append(fd)
	return fdlist



RESULTS_DIRNAME = "../../ba-results/"

def create_lines(infos, yuse):
	'new, then old'
	if len(infos) > 4:
		dirnameNew, dirnameOld, config_filtersNew, config_filtersOld, labels, xattr = tuple(infos[:])
		assert len(labels) == len(config_filtersNew) and len(labels) == len(config_filtersOld)
		ddOld = DirData(RESULTS_DIRNAME + dirnameOld, xattr)
		ddNew = DirData(RESULTS_DIRNAME + dirnameNew, xattr)
		subgroups = []
		for config_filterOld, config_filterNew, label in zip(config_filtersOld, config_filtersNew, labels):
			fdlistNew =_get_fdlist_for_filter_in_dir_data(ddNew, config_filterNew, xattr)
			fdlistOld =_get_fdlist_for_filter_in_dir_data(ddOld, config_filterOld, xattr)
			subgroups.append(Subgroup(fdlistNew, fdlistOld, label, xattr, yuse))
	else:
		dirnameNew, config_filtersNew, labels, xattr = tuple(infos[:])
		assert len(labels) == len(config_filtersNew)
		ddNew = DirData(RESULTS_DIRNAME + dirnameNew, xattr)
		subgroups = []
		for config_filterNew, label in zip(config_filtersNew, labels):
			fdlistNew =_get_fdlist_for_filter_in_dir_data(ddNew, config_filterNew, xattr)
			subgroups.append(Subgroup(fdlistNew, None, label, xattr, yuse))
	lines = []
	for subgroup in subgroups:
		lines.append(subgroup.create_line())
	return lines

# really dirty hack to plots beta values for GA3 adaptive...
def create_lines_beta():
	line = evalplt.Line()
	line.label = "GA3 adaptive"
	for flows in range(100,3001,100):
		yvalues = []
		fin = open("../../ba-results/final/final_ga3b_" + str(flows) + ".dat","r")
		tmp = fin.readline()
		while True:
			try:
				tmp = fin.readline().split(" ")
				i = 0
				while True:
					if tmp[i] == "info:":
						break
					i += 1
				yvalues.append(float(tmp[i-1][:-1]))
			except:
				break
		mean, cihl = ci.calc_sample_mean(yvalues, p=.95)
		settings = util.get_user_settings("representation=ga3b,numFlows=" + str(flows))
		name = "numFlows"
		s = settings[name] if name in settings else util.DEFAULT_DIC[name]
		line.xs.append(s)
		line.ys.append(mean)
		line.yerrs.append(cihl)
	return [line]

infosGAsDefault = ("default", ["representation=ga1","representation=ga2","representation=ga3","representation=greedy"],\
				  ["GA1-default","GA2-default","GA3-default","GreedyFCAPA"], "numFlows")
infosMu = ("population", ["numFlows=1000,representation=ga2", "numFlows=1000,representation=ga3"], ["GA2", "GA3"], "mu")
infosCxpb = ("crossover", ["numFlows=1000,representation=ga2", "numFlows=1000,representation=ga3"], ["GA2", "GA3"], "cxpb")
infosTsize = ("tsize", ["numFlows=1000,representation=ga2", "numFlows=1000,representation=ga3"], ["GA2", "GA3"], "tsize")
infosFlowOrderGA2 = ("floworder", ["representation=ga2","representation=ga2,flowOrder=mostDemanding","representation=ga2b",
												"representation=ga2,flowOrder=random"],
				 ["least dem. first","most dem. first","extended DNA","random"], "numFlows")
infosFlowOrderGA3 = ("floworder", ["representation=ga3","representation=ga3,flowOrder=mostDemanding",
												"representation=ga3,flowOrder=random"],
				 ["least dem. first", "most dem. first","random"], "numFlows")
infosGA3beta = "beta", ["representation=ga3,numFlows=1000"], [u"GA3"], "vcFactor"
#infosGA3vs = ("final", ["representation=ga3","representation=ga3,vcFactor=5.0","representation=ga3b"],
#			  ["GA3-default", u"GA3 with $\\beta$=5", u"GA3 adaptive"], "numFlows")
infosGA3vs = ("final", ["representation=ga3","representation=ga3b"],
			  ["GA3-default", u"GA3 adaptive"], "numFlows")
infosComps6 = ("final", ["dim=6,representation=ga2","dim=6,representation=ga3b","representation=greedy"],
			   ["GA2", "GA3 adaptive", "GreedyFCAPA"], "numFlows")
#infosMutr = ("dmutr", ["representation=ga2,numFlows=1000","representation=ga3b,numFlows=1000",
#										 "representation=ga3,vcFactor=5.0,numFlows=1000"],
#			  ["GA2", u"GA3, $\\beta$=5", "GA3 adaptive"], "mutr")
#infosmuttest6 = ("muttest", ["dim=6,representation=ga2,cxpb=0.99","dim=6,representation=ga3b,cxpb=0.99"],
#			   ["GA2", "GA3 adaptive"], "numFlows")
#infosmuttest10 = ("muttest", ["dim=10,representation=ga2,cxpb=0.99","dim=10,representation=ga3b,cxpb=0.99"],
#			   ["GA2", "GA3 adaptive"], "numFlows")

if __name__ == "__main__":
	#FileData.ASSERT48 = False
	Subgroup.XAXIS_BOUNDS = 0, 3000

	# EDIT THESE THREE LINES FOR CONFIGURATION
	legend_pos = "lower right"   #(0.03, 0.55) 
	use_log_scale, yuse = True, 0 # 0 -> runtime, 2 -> #unsatisfied flows, 3 -> #used LCAs, 4 -> beta (GA3 adaptive)
	infoa = infosComps6 # choose one of the above infos here to create the corresponding plot of the results

	is_relative = len(infoa) > 4
	if yuse == 4:
		lines = create_lines_beta()
	else:
		lines = create_lines(infoa, yuse)
	ylabel = {0: "runtime in s", 2: "# of unsatisfied DFGs", 3: "number of used LCAs",
			  5: "fitness score", 6: "CAs used (%)", 4: "$n_{min}$ value"}[yuse]
	if is_relative:
		ylabel = "relative " + ylabel + " (%)"
	xlabel = {"numFlows": "number of DFGs", "mu": u"population size $\mu$", "cxpb": "crossover probability $p_c$",
			  "tsize": "tournament size", "vcFactor": u"factor $\\beta$ for $n_{min}$", "mutr": u"mutation strenth $\alpha_m$"}[infoa[-1]]
	ycode = {0: "rt", 2: "sat", 3: "CAs", 5: "fit", 6: "CAs_rel", 4: "nmin"}[yuse]
	evalplt.plot_lines_with_err(lines[:], xlabel, ylabel, legend_pos, use_log_scale=use_log_scale, filename=infoa[0]+"_"+ycode+".pdf", showplot=False, columns=1, legend_seperate=True)
