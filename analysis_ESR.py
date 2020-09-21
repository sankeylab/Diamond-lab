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

# Get the axis names
label_s = []
for key in d.ckeys:
    label_s.append(key)

fs = d[0] # Frequency in GHz
total_counts = d[1]# Total counts
etotal_counts = np.sqrt(total_counts) # uncertainty in the count. Assuming poisson

#Get the count rate in count/sec
dt = d.headers['dt_on'] # count time in us
rep = d.headers['repetition']
nb_iter = d.headers['iteration']
count_rate  = total_counts*1e6/(nb_iter*rep*dt) 
ecount_rate = etotal_counts*1e6/(nb_iter*rep*dt) 


# Plot them
import matplotlib.pyplot as plt

plt.figure(tight_layout=True)


plt.errorbar(fs,count_rate*1e-3,yerr=ecount_rate*1e-3)

plt.ylabel("Kcount/sec")
plt.xlabel(label_s[0])
plt.title(d.path, fontsize=9)
