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
PC0     = d[1]
PC0ref  = d[2]
PCpm    = d[3]
PCpmref = d[4]

# Uncertainties
ePC0     = np.sqrt(PC0)
ePC0ref  = np.sqrt(PC0ref)
ePCpm    = np.sqrt(PCpm)
ePCpmref = np.sqrt(PCpmref)

# Get the dfferences and uncertainties
diff_states  = PC0-PCpm
diff_ref     = PC0ref-PCpmref
ediff_states = np.sqrt(ePC0**2 + ePCpm**2)
ediff_ref    = np.sqrt(ePC0ref**2 + ePCpmref**2)

# Plot them
import matplotlib.pyplot as plt



plt.figure(tight_layout=True)
plt.errorbar(t,PC0    ,yerr=ePC0    ,label='ms0')
plt.errorbar(t,PC0ref ,yerr=ePC0ref ,label='ms0_ref')
plt.errorbar(t,PCpm   ,yerr=ePCpm   ,label='ms+-1')
plt.errorbar(t,PCpmref,yerr=ePCpmref,label='ms+-1_ref')
plt.legend()    
plt.xlabel(label_s[0])
plt.ylabel('Total counts')
plt.title(d.path, fontsize=7)


plt.figure(tight_layout=True)
plt.errorbar(t,diff_states, yerr=ediff_states, label='Difference between states')
plt.errorbar(t,diff_ref   , yerr=ediff_ref    ,label='Difference between reference')
plt.legend()    
plt.xlabel(label_s[0])
plt.ylabel('DifferenceTotal counts')
plt.title(d.path, fontsize=7)




