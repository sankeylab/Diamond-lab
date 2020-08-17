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
 
# Extract the data
t = d[0]
PC0 = d[1]
PCp = d[2]
PCm = d[3]
ref = d[4]

# Uncertainties
ePC0 = np.sqrt(PC0)
ePCp = np.sqrt(PCp)
ePCm = np.sqrt(PCm)
eref = np.sqrt(ref)

# Get the dfferences and uncertainties
diffp = PC0-PCp
diffm = PC0-PCm
ediffp = np.sqrt(ePC0**2 + ePCp**2)
ediffm = np.sqrt(ePC0**2 + ePCm**2)

# Plot them
import matplotlib.pyplot as plt



plt.figure(tight_layout=True)
plt.errorbar(t,PC0,yerr=ePC0,label='ms0')
plt.errorbar(t,PCp,yerr=ePCp,label='ms+1')
plt.errorbar(t,PCm,yerr=ePCm,label='ms-1')
plt.errorbar(t,ref,yerr=eref,label='reference')
plt.legend()    
plt.xlabel(label_s[0])
plt.ylabel('Total counts')
plt.title(d.path, fontsize=7)


plt.figure(tight_layout=True)
plt.errorbar(t,diffp,yerr=ediffp,label='Diff_+')
plt.errorbar(t,diffm,yerr=ediffm,label='Diff_-')
plt.legend()    
plt.xlabel(label_s[0])
plt.ylabel('DifferenceTotal counts')
plt.title(d.path, fontsize=7)

















