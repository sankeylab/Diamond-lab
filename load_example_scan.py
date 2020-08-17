# -*- coding: utf-8 -*-
"""
Created on Wed Jul  8 09:23:02 2020

Example of how to load a scan and extract information.

@author: Childresslab
"""

import spinmob as sm
import numpy as np
import matplotlib.pyplot as plt 

d = sm.data.load(text='Select saturation curve ;)')


# Each column of d is a columns of the scan

# We can look at the image by doing this:
plt.pcolor(d)
plt.title(d.path+'\nMethod 1', fontsize=7)


# Or by re-extracting the image
image = []
for col in d:
    image.append(col)
plt.figure()
plt.pcolor(image)
plt.title('Method 2')
plt.title(d.path+'\nMethod 2', fontsize=7)

#
#
## Show them all
#import matplotlib.pyplot as plt
#
#N_slices = slice_s.get_nb_of_slice()
#
#for i in range(1,N_slices):
#    single_slice = slice_s.get_slice(i)
#    PL     = single_slice.Z
#    Vxmin = single_slice.Vxmin
#    Vxmax = single_slice.Vxmax
#    Nx    = single_slice.Nx
#    Vymin = single_slice.Vymin
#    Vymax = single_slice.Vymax      
#    Ny    = single_slice.Ny
#    Vz    = single_slice.Vz
#    label_slice = single_slice.label
#    
#    # Format image nicely with colorbar and true aspect ratio
#    x = np.linspace(Vxmin , Vxmax, Nx)
#    y = np.linspace(Vymin , Vymax, Ny)
#    
#    fig,ax = plt.subplots(figsize = (5,5), dpi=100)
#    pc = ax.pcolor(x, y, PL, cmap='magma')
#    #pc.set_clim(0,100)
#    cb = fig.colorbar(pc)
#    cb.ax.set_ylabel('PL',fontsize=11)
#    ax.set_xlabel('Vx')
#    ax.set_ylabel('Vy')
#    ax.axis('image')
#    ax.set_title(label_slice)
  
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    