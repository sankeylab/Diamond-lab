# -*- coding: utf-8 -*-
"""
Created on Wed Jul  8 09:23:02 2020

Example of how to load a scan and extract information.

@author: Childresslab
"""

import spinmob as sm
import numpy as np
import matplotlib.pyplot as plt 

d = sm.data.load(text='Select Scan')


# Each column of d is a columns of the scan

xmin = d.headers['xmin']
xmax = d.headers['xmax']
Nx   = d.headers['Nx']
labelX = d.headers['labelX']
ymin = d.headers['ymin']
ymax = d.headers['ymax']
Ny   = d.headers['Ny']
labelY = d.headers['labelY']

xs = np.linspace(xmin, xmax, Nx)
ys = np.linspace(ymin, ymax, Ny)

# We can look at the image by doing this:
fig = plt.figure()
ax = fig.add_subplot(111)
ax.pcolor(xs, ys,d)
ax.set_xlabel(labelX)
ax.set_ylabel(labelY)
ax.set_aspect('equal')
plt.title(d.path, fontsize=9)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    