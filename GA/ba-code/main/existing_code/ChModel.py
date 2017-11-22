from __future__ import division
import math
import random

# bandwidth in mhz
bs_bandwidth = 20 * 1000000


def w2db(watts):
    return 10 * math.log(watts, 10)

def db2w(db):
    return math.pow(10, db / 10)	


def coupling_loss_db(distance):
    # lognormal fading, only valid for macro cells:
    # http://www.etsi.org/deliver/etsi_tr/136900_136999/136931/09.00.00_60/tr_136931v090000p.pdf
    # fading = random.normalvariate(0, 10)
    # Winner-II model:
    # free space, 2 ghz, according to
    # http://www.raymaps.com/index.php/winner-ii-path-loss-model/
    #pl = 20*math.log(distance, 10) + 46.4 + 20 * math.log(2/5.0, 10) + fading
	
    max_gain = 5.0
    wall_penetration = 20.0
    pathloss_constant = 128.1
    pathloss_factor = 37.6
    conn_shadow = random.normalvariate(0, 10)
    user_pos_shadow = random.normalvariate(0, 10)
    shadowing = (conn_shadow + user_pos_shadow) / math.sqrt(2)
	
    pl = -max_gain + pathloss_constant + pathloss_factor * math.log(distance/1000, 10) + shadowing + wall_penetration
    return pl


def signal_power_db():
    tx_power = 49
    return tx_power


def received_signal_power_db(distance):
    s_power = signal_power_db() - coupling_loss_db(distance)
    return s_power


def received_signal_power_watts(distance):
    return db2w(received_signal_power_db(distance))


# def noise_watts():
    # noisepsdwph = 3.9810717055349565e-21
    # iwph = 1.2549314403283351e-18
    # return bs_bandwidth * (noisepsdwph + iwph)
	
def noise_watts():
    # noisepsdwph = 3.9810717055349565e-21
    # return bs_bandwidth * noisepsdwph
	return db2w(-174 + w2db(bs_bandwidth) + 9)
	
def interference_watts(rspw, c, no_bs):
	return sum(rspw[i][1] for i in range(c, no_bs))

# def sinr(distance):
    # return w2db(received_signal_power_watts(distance) / noise_watts())
	
def sinr(rspw, c, no_bs):
    return w2db(sum(rspw[i][1] for i in range(0,c)) / ( interference_watts(rspw, c, no_bs) + noise_watts() ) )


# def shannon_capacity(distance):
    # """
    # @param distance: meters between bs and ue
    # @return: the channel capacity in bits per second
    # """
    # capacity = bs_bandwidth * math.log(1 + (received_signal_power_watts(distance) / noise_watts()), 2)  # bit/s

    # return capacity
	
def shannon_capacity(rspw, c, no_bs):
    """
    @param distance: meters between bs and ue
    @return: the channel capacity in bits per second
    """
    return bs_bandwidth * math.log( 1 + sum(rspw[i][1] for i in range(0,c)) / ( interference_watts(rspw, c, no_bs) + noise_watts() ), 2)  # bit/s
	
	
if __name__ == "__main__":
    import doctest

    distance=100
    # print "PL", coupling_loss_db(distance)
    # print "RX",received_signal_power_db(distance)
    # print "DR", shannon_capacity(distance), "bit/s"
    # print "SINR", sinr(distance)
