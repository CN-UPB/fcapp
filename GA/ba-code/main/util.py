from cStringIO import StringIO
import os
import sys
from mycode import settings
from mycode.cpp_network import CppNetwork
from mycode.settings import config
from mycode.utilf import println

DEFAULT_CONFIG = "flowOrder=leastDemanding,useHopPathLength=0,parentSelection=tournament"
DEFAULT_CONFIG += ",mu=20,cxpb=.2,mutr=.15,survivorSelection=best,tsize=2,vcFactor=1.0"
DEFAULT_CONFIG += ",controllerProb=.6,terminationMaxCounter=15"
DEFAULT_CONFIG += ",dim=6,numFlows=1,bFlowFactor=1.0"
DEFAULT_CONFIG += ",fitness4th=none,representation=ga1"

"""alternatives
bFlowFactor=20.0
useHopPathLength=1
"""

def create_cn(config_dic):
	dim, num_flows = map(int, [config_dic["dim"], config_dic["numFlows"]])
	mesh_filename = config.RES_ROOT + "../../ba-networks/{}-{}-{}".format(dim, num_flows, config.PROC_ID)
	mesh_file = open(mesh_filename)
	cn = CppNetwork()
	cn.generate_from_file(mesh_file)
	return cn, mesh_filename

def get_updated_config_dic(user_dic):
	config_dic = create_dict_from_string(DEFAULT_CONFIG)
	for k, v in user_dic.iteritems():
		assert(k in config_dic)
		config_dic[k] = v
	return config_dic

def set_settings():
	config.RES_ROOT = os.path.dirname(os.path.realpath(__file__)) + "/"
	config.PROC_ID = int(sys.argv[1])
	config_dic = get_updated_config_dic(user_dic=create_dict_from_string(sys.argv[2]))

	config.USE_HOP_PATH_LENGTH = bool(int(config_dic["useHopPathLength"]))
	config.CONTROLLER_PROB = float(config_dic["controllerProb"])
	config.MU = int(config_dic["mu"])
	config.CXPB = float(config_dic["cxpb"])
	config.MUTR = float(config_dic["mutr"])
	config.TSIZE = int(config_dic["tsize"])
	config.PARENT_SELECTION = config_dic["parentSelection"]
	config.SURVIVOR_SELECTION = config_dic["survivorSelection"]
	config.TERMINATION_MAX_COUNTER = int(config_dic["terminationMaxCounter"])
	config.FLOW_ORDER = config_dic["flowOrder"]
	config.VC_FACTOR = float(config_dic["vcFactor"])
	config.FITNESS_4TH = config_dic["fitness4th"]
	config.REPRESENTATION = config_dic["representation"]

	config.MUTPB = 1.0 - config.CXPB
	config.LAMBDA = config.MU

	assert config.FLOW_ORDER in ("leastDemanding", "mostDemanding", "random", "closestCLC")
	assert config.SURVIVOR_SELECTION in ("tournament", "best")
	assert config.FITNESS_4TH in ("none", "min", "mean")
	assert config.REPRESENTATION in ("ga1", "ga2", "ga3", "ga2b", "ga3b", "greedy")

	return config_dic

def create_dict_from_string(s):
	dic = {}
	if not "," in s and not "=" in s:
		return dic
	for pair in s.split(","):
		k, v = pair.split("=")
		dic[k] = v
	return dic


def print_cpg(cpg):
	println("State: " + cpg.state)
	if cpg.state == "NOT SOLVED":
		print("Remaining nodes: " + str([i for i in cpg.cn.V if not i in cpg.Controlled]))
	println("CRCs: " + str(len(cpg.CRCs)) )
	println(str(cpg.CRCs))
	println("CLCs: " + str(len(cpg.CLCs)) + " (out of " + str(len(cpg.cn.C)) + " available)")
	println(str(cpg.CLCs))
	println("Flows satisfied: " + str(len(cpg.Satisfied)) + " out of " + str(len(cpg.cn.F)))


def cast_dic_entries(dic):
	for k in ("useHopPathLength","elitistSurvivorSelection"):
		if k in dic:
			dic[k] = bool(int(dic[k]))
	for k in ("mu","tsize","terminationMaxCounter","dim","numFlows"):
		if k in dic:
			dic[k] = int(dic[k])
	for k in ("cxpb","mutr","vcFactor","controllerProb","bFlowFactor"):
		if k in dic:
			dic[k] = float(dic[k])
	pass


def get_user_settings(config_str, xattr=None):
	user_dic = create_dict_from_string(config_str)
	default_dic = create_dict_from_string(DEFAULT_CONFIG)
	tbd = []

	for k in user_dic:
		assert(k in default_dic)
		if user_dic[k] == default_dic[k] and k != xattr:
			tbd.append(k)
	for k in tbd:
		del user_dic[k]
	cast_dic_entries(user_dic)
	return user_dic

def get_default_dic():
	dic = create_dict_from_string(DEFAULT_CONFIG)
	cast_dic_entries(dic)
	return dic

DEFAULT_DIC = get_default_dic()