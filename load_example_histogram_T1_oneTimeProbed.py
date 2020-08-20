# -*- coding: utf-8 -*-
"""
Created on Wed Jul  8 07:57:17 2020

Example of how to load the saturation curve

@author: Childresslab
"""



import spinmob as sm
import numpy as np


d = sm.data.load(text='Select saturation curve ;)')

# Check the ckeys
print(d.ckeys)



# Plot them
import matplotlib.pyplot as plt

plt.figure(tight_layout=True)

# Get the axis names
label_s = []
for key in d.ckeys:
    label_s.append(key)
    # Print the mean
    txt = 'Mean of '+key+' = %f'%np.mean(d[key])
    print(txt)
    # Show the histogram
    plt.hist(d[key], bins=100, label=txt)
    
plt.legend()
plt.xlabel('Count per iteration')
plt.ylabel('Occurence')

plt.title(d.path, fontsize=7)


#plt.hist(d['ms-1'], bins=100)
#plt.hist(d['ms+1'], bins=100)
#plt.hist(d['ref'], bins=100)