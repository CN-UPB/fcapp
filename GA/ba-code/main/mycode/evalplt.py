import numpy as np
import matplotlib.pyplot as plt

plot_path = "../../diss_plots/"

class Line(object):
	def __init__(self):
		self.xs = []
		self.ys = []
		self.yerrs = []
		self.label = "<todo>"

def plot_lines_with_err(lines, xlabel, ylabel, legend_position, use_log_scale=False, filename="plot.pdf", showplot=True, columns=1, legend_seperate=False):
	'each line must have x array, y, and yerr'

	fig, ax = plt.subplots()
	#ax.xaxis.get_major_formatter().set_powerlimits((0, 1))
	ax.yaxis.get_major_formatter().set_powerlimits((0, 13))
	if use_log_scale:
		ax.set_yscale('log')
	#ax.set_title('Vert. symmetric')
	plt.xlabel(xlabel, fontsize=24)
	plt.ylabel(ylabel, fontsize=24)
	plt.tick_params(axis='both', which='major', labelsize=14)
	plt.tick_params(axis='both', which='minor', labelsize=12)
	plines = []
	plabels = []

	for line, fmt in zip(lines, ["rs--", "go--", "bd--", "yD--"]):
		pl = ax.errorbar(line.xs, line.ys, yerr=line.yerrs, fmt=fmt, label=line.label)
		plines.append(pl[0])
		plabels.append(line.label)
	xa, xb = plt.xlim()
	xd = .05 * (xb - xa)
	plt.xlim(xa + .5*xd, xb + xd)
	#plt.xlim(1450,2550)
	
	if legend_seperate == False:
		plt.legend(loc=legend_position, prop={'size':16}, ncol=columns)
		if showplot == True:
			plt.show()
		else:
			plt.savefig(plot_path + filename, bbox_inches='tight')
	else:
		if showplot == True:
			plt.show()
		else:
			plt.savefig(plot_path + filename, bbox_inches='tight')
		F = plt.figure(2)
		F.legend(plines,plabels,prop={'size':16}, ncol=columns)
		plt.savefig(plot_path + 'plot_legend.pdf', bbox_inches='tight')
		