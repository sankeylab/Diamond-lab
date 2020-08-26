# -*- coding: utf-8 -*-
"""
Created on Wed Aug 26 09:11:39 2020

@author: Childresslab
"""

import numpy as np
from spinmob import egg

import traceback
_p = traceback.print_last #Very usefull command to use for getting the last-not-printed error


# Debug stuff.
_debug_enabled     = False

def _debug(*a):
    if _debug_enabled: 
        s = []
        for x in a: s.append(str(x))
        print(', '.join(s))
        

 
class map2D(egg.gui.Window):
    """
    GUI of a 2D heat map .
    """
    
    def __init__(self, name="Great mapper", size=[1000,500]): 
        """
        Yo. 
        """    
        _debug('map2D:__init__')
        _debug('Make each day your masterpiece. – John Wooden')
        
        # Run the basic stuff for the initialization
        egg.gui.Window.__init__(self, title=name, size=size)
        
        # Get all the colormaps that we defined
        self.colormaps = PersonalColorMap()

        # A plot item for showing the incoming data
        self.plot_item = egg.pyqtgraph.PlotItem()
        self.plot_image = egg.pyqtgraph.ImageView(view=self.plot_item)
        self.place_object(self.plot_image, alignment=0)  
        
        # Attribute usefull for the map
        self.scaleX = 1
        self.scaleY = 1
        self.posX   = 0
        self.posY   = 0
        self.labelX = 'I am x'
        self.labelY = 'Its me, y'
      
        # Add a dummy map 
        x = np.linspace(1, 20, 100)
        y = np.linspace(1, 20, 100)
        X,Y = np.meshgrid(x,y)
        self.Z = np.cos(X*2)*np.sin(Y)*X*Y  
        
        # Set the map
        self.set_data(self.Z, 
                      (x.min(), x.max(), len(x)), 
                      (y.min(), y.max(), len(y)))    
        

        

    def set_data(self, Z, 
                 x_info=-1, y_info=-1,
                 label_x=-1, label_y=-1, 
                 color=-1):
        """
        Set the data on the map. 
        
        Z:
            Nx X Ny grid of data to plot. 
            
        x_info:
            Tuple (xmin, xmax, Nx), where xmin is the minimum of the x axis, 
            xmax is the maximum and Nx is the number of point
        y_info:
            Tuple (ymin, ymax, Ny), where ymin is the minimum of the y axis, 
            ymax is the maximum and Ny is the number of point
        label_x:
            String. Label on the x axis
        label_y:
            String. Label on the y axis    
        color:
            (string) name of the colormap to use.See the method set_colormap for 
            more info. 
            
        """
        _debug('map2D: set_data')
        
        self.Z = Z
        
        # Extract the information on the axis if specified 
        if x_info != -1:
            self.xmin = x_info[0]
            self.xmax = x_info[1]
            self.Nx   = x_info[2]
            # Get the attribute relevant for the map object
            self.scaleX = (self.xmax - self.xmin)/self.Nx
            self.posX = self.xmin
        if y_info != -1:
            self.ymin = y_info[0]
            self.ymax = y_info[1]
            self.Ny   = y_info[2]
            # Get the attribute relevant for the map object
            self.scaleY = (self.ymax - self.ymin)/self.Ny
            self.posY = self.ymin     
        if label_x != -1:
            self.labelX = label_x
            self.plot_item.setLabel('bottom', text=self.labelX)
        if label_y != -1:
            self.labelY = label_y   
            self.plot_item.setLabel('left'  , text=self.labelY) 
        if color != -1:
            self.set_colormap(color)
                   
        # Update the image
        self.plot_image.setImage(self.Z.T,
                                 pos=(self.posX, self.posY),
                                 scale =(self.scaleX, self.scaleY))      
        # scale/pan the view to fit the image.
        self.plot_image.autoRange()
        # Set the aspect ratio to false for not having the image to scale
        self.plot_image.view.setAspectLocked(False)     
        
    def get_list_colormap(self):
        """
        Return the list of the possible colormap
        """
        _debug('map2D: get_list_colormap')
        return self.colormaps.get_list_colormaps()
    
    def set_colormap(self, name):
        """
        Set the colormap.
        
        name:
            (String) Name of the color map. It must be contained in the list 
            returned by the method get_list_colormap.
        """
        _debug('map2D: set_colormap')
        mycmap = self.colormaps.get_colormap(name)
        self.plot_image.setColorMap(mycmap)
        

        
class PersonalColorMap():
    """
    This class is aimed to store various colormap that we would like to use. 
    """
    def __init__(self):
        """
        """
        
        # Contains all the name of the color map that we have. 
        self.list_colormaps = ['Awesome', 
                               'old_time',
                               'stairway_to_heaven',
                               'halloween',
                               'fear_of_the_dark',
                               'sonic_supersonic',
                               'ca_va_bien_aller']
        
    def get_list_colormaps(self):
        return self.list_colormaps
    
    def get_colormap(self, name):
        """
        name:
            String contained in list_colormaps. 
            
        """
        if name == 'Awesome':
            return self.awesome()
        if name == 'old_time':
            return self.old_time()
        if name == 'halloween':
            return self.halloween()
        if name == 'stairway_to_heaven':
            return self.heaven()
        if name == 'sonic_supersonic':
            return self.sonic_supersonic()
        if name == 'ca_va_bien_aller':
            return self.ca_va_bien_aller()
        if name == 'fear_of_the_dark':
            return self.black_red_black()
        
    def awesome(self):
        """
        This is in the pyqtgraph example
        """
        
        colors = [
            (0, 0, 0),
            (45, 5, 61),
            (84, 42, 55),
            (150, 87, 60),
            (208, 171, 141),
            (255, 255, 255)
        ]
        
        return egg.pyqtgraph.colormap.ColorMap(pos=np.linspace(0.0, 1.0, 6), color=colors)
        
    def old_time(self):
        """
        Black and white. 
        """
        colors = [
                (0, 0, 0),
                (255, 255, 255)]
        
        return egg.pyqtgraph.colormap.ColorMap(pos=np.linspace(0.0, 1.0, 2), color=colors)
        
    def halloween(self):
        """
        Black to orange to red
        """        
        colors = [
                (0, 0, 0),
                (255, 127, 39),
                (255, 0, 0)]
        
        return egg.pyqtgraph.colormap.ColorMap(pos=np.linspace(0.0, 1.0, 3), color=colors)        

    def heaven(self):
        """
        White to yellow to cyan
        """        
        colors = [
                (255, 255, 255),
                (255, 255, 20),
                (0, 255, 255)]
        
        return egg.pyqtgraph.colormap.ColorMap(pos=np.linspace(0.0, 1.0, 3), color=colors) 
    
    def black_red_black(self):
        """
        Black, red in the middle, black again
        """
        colors = [
                (0, 0, 0),
                (255, 127, 39),
                (255, 0, 0),
                (255, 127, 39),
                (0, 0, 0)]
        
        return egg.pyqtgraph.colormap.ColorMap(pos=np.linspace(0.0, 1.0, len(colors)), color=colors)  
    
    
    def sonic_supersonic(self):
        """
        White to yellow to blue
        """        
        colors = [
                (255, 255, 255),
                (155, 155, 0),
                (0, 0, 200)]
        
        return egg.pyqtgraph.colormap.ColorMap(pos=np.linspace(0.0, 1.0, 3), color=colors) 
    
    def ca_va_bien_aller(self):
        """
        Rainbow 
        """
        
        colors = [
                (255, 0, 0),
                (255, 255, 0),
                (0, 255, 0),
                (0, 255, 255),
                (0, 0, 255),
                (255, 0, 255)]
        
        return egg.pyqtgraph.colormap.ColorMap(pos=np.linspace(0.0, 1.0, len(colors)), color=colors)    
        
        
if __name__ == '__main__':
    _debug_enabled     = True
    
    
    self = map2D()
    self.show()
    
    list_color = self.get_list_colormap()
    print('List of colormap = ', list_color)
    
    # Try some data
    ts = np.linspace(5, 20, 1000)
    
    x = np.linspace(-20, 20, 200)
    y = np.linspace(-20, 20, 200)
    X,Y = np.meshgrid(x,y)
    
    Gauss = 0
    for t in ts:
        x1 = t*np.cos(t)
        y1 = t*np.sin(t)        
        Gauss_t = np.exp(-( (X-x1)**2+(Y-y1)**2 )/4)
        Gauss += Gauss_t
        
    Z = Gauss
    
    self.set_data(Z, (x.min(), x.max(), len(x)), (y.min(), y.max(), len(y)),
                  'Hey x', 'Holla y')
    
    self.set_colormap('ca_va_bien_aller')
    
    
    
    
    
    