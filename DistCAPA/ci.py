#!/usr/bin/env python

from scipy import stats
from math import sqrt
import numpy

def ci_stat(sd, n, p=0.95):
    """
    Computes a confidence interval
    sd: standard deviation
    n: sample size
    p: confidence level, e.g., 0.99, 0.95, 0.90
    """

    if n < 2 or int(n) != n:
        raise ValueError, 'ci: n must be an integer > 1'

    # degrees of freedom
    df = n-1

    # alpha
    a = (1.0-p)

    # standard error
    se = sd / sqrt(n)

    # t value
    t = abs(stats.t.ppf(a/2.0, df))

    # confidence interval half length
    h = se * t

    return(h)

def ci_data (data, p=0.95):
    """
    Computes a confidence interval from samples
    data: list containing input data
    p: confidence level, e.g., 0.99, 0.95, 0.90
    """

    # create numpy array
    a = numpy.array(data)

    # get sample size
    n = a.size

    # get standard deviation
    sd = numpy.std(a)

    return(ci_stat(sd, n, p))

def calc_sample_mean (inputData, p):
    """
    Aggregate samples by returning mean and ci
    inputData: dict containing list of samples
    p: confidence level, e.g., 0.99, 0.95, 0.90
    """

    # iterate over x values
    arr = numpy.array(inputData)
    mean  = numpy.mean(arr)
    confi = ci_data(arr, p)
	#print "{0}, {1}, {2}".format(x, Y[-1], E[-1])

    return(mean, confi)
