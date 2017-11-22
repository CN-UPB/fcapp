
# all should be set externally
class config(object):
	RES_ROOT = None
	PROC_ID = -1
	DEFAULT_P_NODE = 2.e11
	NGEN = 20000
	# NGEN = 2

	NN_MINIMUM_SIGMA = 1.0
	CONTROLLER_PROB = .6
	TERMINATION_MAX_COUNTER = 15
	TSIZE = 2
	SURVIVOR_SELECTION = "best"
	VC_FACTOR = 3.1

	MU = 50
	CXPB = .1
	MUTR = .15
	FLOW_ORDER = "leastDemanding"
	#FLOW_ORDER = "leastDemanding", "mostDemanding", "largestPUB", "closestCLC"
	USE_HOP_PATH_LENGTH = False  # hops vs lat sum
	PARENT_SELECTION = "tournament"
	#PARENT_SELECTION = "fitnessProportional"
	FITNESS_4TH = "none"
	#FITNESS_4TH = "none", "mean", "min"
	REPRESENTATION = "ga1"
	#REPRESENTATION = "ga1", "ga2", "ga2b", "ga3", "ga3b"

	MUTPB = -1
	LAMBDA = -1

