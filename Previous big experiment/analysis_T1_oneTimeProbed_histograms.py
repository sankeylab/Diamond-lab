# -*- coding: utf-8 -*-
"""
Created on Wed Jul  8 07:57:17 2020

Example of how to load the saturation curve

@author: Childresslab
"""



import spinmob as sm
import numpy as np
import matplotlib.pyplot as plt

import scipy.optimize as opt

d = sm.data.load(text='Select saturation curve ;)')

# Check the ckeys
print(d.ckeys)
# CHeck the headers
print(d.hkeys)

# Extract usefull info
rep = d.headers['repetition']


# Set to True the data to check 
show_ms_0  = True
show_ms_m1 = False 
show_ms_p1 = True
show_ref   = True

# In the ckeys the order should match the order of the following list
show_list = [show_ms_0, show_ms_m1, show_ms_p1, show_ref]




# Plot the distributions filled
plt.figure(tight_layout=True)
for i, key in enumerate(d.ckeys):
    # Only show the one selected
    if show_list[i]:
        # Process each columns
        mean = np.mean(d[key])/rep
        std  = np.std (d[key])/rep
        # Print the mean
        txt = 'Mean of '+key+' = %f +- %f'%(mean,std)
        print(txt)
        
        bin_edges = np.linspace(mean-3*std, mean+3*std, 25)
        # Show the histogram
        plt.hist(d[key]/rep, bins=bin_edges, label=txt, alpha=0.5)
    
    
    
plt.legend()
plt.xlabel('Count per readout of %.1f ns'%(d.headers['dt_readout']*1e3))
plt.ylabel('Occurence')

plt.title(d.path+'\nTime probed %.1f us'%d.headers['t_probe'],
          fontsize=9)






# Plot the distributions not filled
plt.figure(tight_layout=True)
for i, key in enumerate(d.ckeys):
    # Only show the one selected
    if show_list[i]:
        # Process each columns
        mean = np.mean(d[key])/rep
        std  = np.std (d[key])/rep
        # Print the mean
        txt = 'Mean of '+key+' = %f +- %f'%(mean,std)
        print(txt)
        # Show the histogram
        hist, bin_edges  = np.histogram(d[key]/rep, bins=100)
        x = (bin_edges[1:] + bin_edges[:-1])/2 # takethe center of the bins
        plt.plot(x, hist, label=txt)

plt.legend()
plt.xlabel('Count per readout of %.1f ns'%(d.headers['dt_readout']*1e3))
plt.ylabel('Occurence')

plt.title(d.path+'\nTime probed %.1f us'%d.headers['t_probe'],
          fontsize=9)

# Fit the distribution
#TODO fit them !




#plt.hist(d['ms-1'], bins=100)
#plt.hist(d['ms+1'], bins=100)
#plt.hist(d['ref'], bins=100)