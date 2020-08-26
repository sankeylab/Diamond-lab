# -*- coding: utf-8 -*-
"""
Created on Wed Jul  8 07:57:17 2020

Example of how to load the saturation curve

@author: Childresslab
"""



import spinmob as sm
import numpy as np
import matplotlib.pyplot as plt

d = sm.data.load(text='Select saturation curve ;)')

# Check the ckeys
print(d.ckeys)
# CHeck the headers
print(d.hkeys)

# Extract usefull info
rep = d.headers['repetition']


# Plot them
plt.figure(tight_layout=True)
for key in d.ckeys:
    # Process each columns
    # Print the mean
    txt = 'Mean of '+key+' = %f'%(np.mean(d[key]/rep))
    print(txt)
    # Show the histogram
    plt.hist(d[key]/rep, bins=100, label=txt)
    
plt.legend()
plt.xlabel('Count per readout of %.1f ns'%(d.headers['dt_readout']*1e3))
plt.ylabel('Occurence')

plt.title(d.path+'\nTime probed %.1f us'%d.headers['t_probe'],
          fontsize=9)


#plt.hist(d['ms-1'], bins=100)
#plt.hist(d['ms+1'], bins=100)
#plt.hist(d['ref'], bins=100)