# -*- coding: utf-8 -*-
"""
Created on Mon Dec 12 11:12:16 2016

Check the contrast between two spin state initialization. 

@author: Adrian Solyom modified by Michael
"""

import spinmob as sm
import numpy as np
import matplotlib.pyplot as plt



# Open data file
d = sm.data.load(text="Load spin contrast data :3",
                 filters="*.dat")
# Check the ckeys
print(d.ckeys)



    

counts0 = d[1]
counts1 = d[2]



# Delay before laser turns on, ns
init_delay = float(input("Give delay before laser turns on, (ns):\t"))

Ticks = len(d[0])
t_ns = d[0]*1e3 - init_delay


read0 = counts0
read1 = counts1
readsig = read0-read1

readSNR = np.zeros((Ticks,Ticks))
readcontrast = np.zeros((Ticks,Ticks))

# Loop over starting tick
for i in np.arange(Ticks):
    
    # Loop over ending tick
    for j in np.arange(Ticks):
        
        # Only make a comparison if j > i
        if j>i:
            
            # Define signal per readout (0 - 1)/Nreads
            read_signal = np.sum(readsig[i:j])
            
            # Define noise as sqrt(total counts in readout)
            read_noise = np.sqrt(np.sum(read0[i:j]))
            
            readSNR[i,j] = read_signal/read_noise
            readcontrast[i,j] = read_signal/np.sum(read0[i:j])

t_final = t_ns[readSNR[0].argmax()]

# Make figures showing SNR and contrast as a function of counting gate times

fig3, axs = plt.subplots(2,sharex=True)
axs[0].plot(t_ns, read0, t_ns, read1, t_ns, readsig)
axs[0].plot((t_final,t_final),((0,read0.max())),'r')
axs[0].set_ylabel('Counts per tick\nper readout')

axs[1].plot(t_ns[t_ns > 0], readSNR[0][t_ns > 0], color='C0')
axs[1].plot((t_final,t_final),((0,readSNR[0].max())),'r')
axs[1].set_ylabel('Signal to noise level\nper readout')
axs[1].set_xlabel('Time after laser turned on (ns)')
axs[1].tick_params(axis='y', colors='C0')
axs[1].set_ylim(0,None)

index = np.argmax(readcontrast[0][t_ns > 0])
xmax = t_ns[t_ns > 0][index]
ymax = readcontrast[0][t_ns > 0][index]*100

axCon = axs[1].twinx()
axCon.plot(t_ns[t_ns > 0], readcontrast[0][t_ns > 0]*100, color='C1')
axCon.plot(xmax,ymax, 'ro',markersize=7)
axCon.text(xmax,ymax, 'xmax = %.2f\nymax = %.2f'%(xmax,ymax), size=7, color='k')
axCon.set_ylabel('Contrast (%)')
axCon.tick_params(axis='y', colors='C1')
axCon.set_ylim(0,None)
axCon.spines['right'].set_color('C1')
axCon.spines['left'].set_color('C0')


fig3.tight_layout()

axs[0].legend(['ms=0','ms=-1','Signal'])