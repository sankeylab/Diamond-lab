# -*- coding: utf-8 -*-
"""
Created on Thu Aug 27 13:13:42 2020

Goal:
    Define some functions for making and viewing the lines to sweep with the
    magnet. 

@author: Childresslab
"""

import numpy as np
import spinmob as _s

from mpl_toolkits.mplot3d import Axes3D # This import registers the 3D projection, but is otherwise unused.
import matplotlib.pyplot as plt

#TODO create a general function for a plane perpendicular to a given normal direction

def tilted_plane():
    """
    Make a plabe tilted with respect to the axis. 
    It's gonna be a zigzag in the plane
    """
    xs = []
    ys = []
    zs = []

    # Define a plane tilted
    x1 = 10
    x2 = 17
    z1 = 15
    z2 = 22
    y_lines = np.linspace(14, 19, 10)
    
    for i in range(int(len(y_lines)/2)):
        
        y1 = y_lines[2*i]
        y2 = y_lines[2*i+1]
        
        xs.append(x1)
        xs.append(x2)
        ys.append(y1)
        ys.append(y2)
        zs.append(z1)
        zs.append(z2)    
        
    return xs, ys, zs

def parallel_plane():
    """
    Make a plane parallel to an axis.
    It's gonna be a zigzag in the plane.
    """
    xs = []
    ys = []
    zs = []

    # Define a plane tilted
    y1 = 14
    y2 = 16.7
    z1 = 17.5
    z2 = z1
    x_lines = np.linspace(14, 19, 10)
    
    for i in range(int(len(x_lines)/2)):
        x1 = x_lines[2*i]
        x2 = x_lines[2*i+1]
        
        xs.append(x1)
        xs.append(x2)
        ys.append(y1)
        ys.append(y2)
        zs.append(z1)
        zs.append(z2)    
        
    return xs, ys, zs


#By default set the object
if __name__ == '__main__':
    _debug_enabled = True    

#    xs, ys, zs = tilted_plane()
    xs, ys, zs = parallel_plane()
    
    # Save the data into a databox
    databox = _s.data.databox()
    # Put some header
    databox.insert_header('name', 'Hakuna matata')
    # Add each column
    databox['xs'] = xs
    databox['ys'] = ys
    databox['zs'] = zs  
    # Save it
    databox.save_file()


    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')   
    ax.plot(xs, ys, zs, label='Goal') 
    ax.scatter(xs[1:-1], ys[1:-1], zs[1:-1], '-r') 
    ax.scatter(xs[0], ys[0], zs[0]   , color='red',label='Start')
    ax.scatter(xs[-1], ys[-1], zs[-1], color='y'  ,label='End')
    plt.legend()
    ax.set_xlabel('x (mm)')
    ax.set_ylabel('y (mm)')
    ax.set_zlabel('z (mm)')
    # Set equal aspect
    # For this we need the extermum of all the pts
    allpts = np.concatenate((xs, ys, zs))
    maximum = np.max(allpts)
    minimum = np.min(allpts)
    ax.set_xlim3d(minimum, maximum)
    ax.set_ylim3d(minimum, maximum)
    ax.set_zlim3d(minimum, maximum)















