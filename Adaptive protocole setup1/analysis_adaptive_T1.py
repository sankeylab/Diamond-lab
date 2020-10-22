# -*- coding: utf-8 -*-
"""
Created on Wed Jul  8 07:57:17 2020

Example of how to load the saturation curve

@author: Childresslab
"""



import spinmob as sm
import numpy as np
import matplotlib.pyplot as plt


d = sm.data.load(text='Select the data', quiet=False)

# Check the ckeys
print('ckeys:')
print(d.ckeys)
# CHeck the headers

print()
print('hkeys:')
print(d.hkeys)


ts = d['t_probe_s']

count_ms0  = d['measure_ms0']
count_msp  = d['measure_msp_s']
N_readouts = d['N_readout_s']


diffs  = count_ms0 - count_msp
ediffs = np.sqrt( count_ms0/N_readouts + count_msp/N_readouts )


# Plot the probed times
plt.figure(tight_layout=True)
plt.errorbar(ts*1e3, diffs, yerr=ediffs, marker='.', linestyle='')

plt.xlabel('Time probed (ms)')
plt.ylabel('Measured diff')
plt.title(d.path, fontsize=9)



# Plot the rates
iter_s = d['iteration_s_s']
gp_s = d['best_gp_s']
gm_s = d['best_gp_s']
egp_s = d['std_gp_s']
egm_s = d['std_gp_s']


plt.figure(tight_layout=True)
plt.errorbar(iter_s, gp_s, yerr=egp_s, marker='.', linestyle='',label='Gp')
plt.errorbar(iter_s, gm_s, yerr=egm_s, marker='.', linestyle='',label='Gm')

plt.xlabel('Iteration')
plt.ylabel('Rates (Hz')


















