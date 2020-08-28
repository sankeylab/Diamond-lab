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

import traceback
_p = traceback.print_last #Very usefull command to use for getting the last-not-printed error

# Debug stuff.
_debug_enabled                = False

def _debug(*a):
    if _debug_enabled: 
        s = []
        for x in a: s.append(str(x))
        print(', '.join(s))

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
    z1 = 23
    z2 = z1
    x_lines = np.linspace(14, 19, 4)
    
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


def plot_magSweepLinesSettings(databox, title='Patate Chaude'):
    """
    Plot the lines that we aim to sweep. 
    """
    
    xs = databox['xs']
    ys = databox['ys']
    zs = databox['zs']   

    # Initialize the figure and axis
    fig = plt.figure(tight_layout=True)
    ax  = fig.add_subplot(111, projection='3d') 

    ax.plot(xs, ys, zs, label='Goal') 
    ax.scatter(xs[1:-1], ys[1:-1], zs[1:-1]) 
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
    # Slice the title if it's too long (for example, by including the whol path)
    if len(title)>20:
        t1 = title[:int(len(title)/2)]
        t2 = title[int(len(title)/2):]
        title = t1+'\n'+t2
        
    ax.set_title(title, fontsize=10) 

def plot_magSweepLinesResult(dataResult, settings=-1, title='Patate Chaude'):
    """
    Plot the result of a sweep
    
    #TODO EXPLAIN THE INPUT
    
    """
    
    xs = dataResult['xs']
    ys = dataResult['ys']
    zs = dataResult['zs']   
    ws = dataResult['ws'] # The color of the point will be that

    # Initialize the figure and axis
    fig = plt.figure(tight_layout=True)
    ax  = fig.add_subplot(111, projection='3d') 

    ax.scatter(xs, ys, zs, c=ws,label='Scanned points') 
    if settings !=-1:
        # Show the settings if we input some
        xs_goal = settings['xs']
        ys_goal = settings['ys']
        zs_goal = settings['zs']
        ax.plot(xs_goal[1:-1], ys_goal[1:-1], zs_goal[1:-1], label='Goal') 
        ax.scatter(xs_goal[0], ys_goal[0], zs_goal[0]   , color='red',label='Start')
        ax.scatter(xs_goal[-1], ys_goal[-1], zs_goal[-1], color='y'  ,label='End')        
        
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
    # Slice the title if it's too long (for example, by including the whol path)
    if len(title)>20:
        t1 = title[:int(len(title)/2)]
        t2 = title[int(len(title)/2):]
        title = t1+'\n'+t2
        
    ax.set_title(title, fontsize=10)     

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

    plot_magSweepLinesSettings(databox, 'My path')
















