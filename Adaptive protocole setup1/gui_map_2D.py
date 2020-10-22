# -*- coding: utf-8 -*-
"""
Created on Wed Aug 26 09:11:39 2020

@author: Childresslab
"""

import numpy as np
from spinmob import egg
import spinmob as sm

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
        
        # Place a combo box for the colormap
        # It's not the best way to do it for now, but it gonna do the job for now. 
        self.list_colormap = self.colormaps.get_list_colormaps()
        self.comboxBox_colormap = egg.gui.ComboBox(items=self.list_colormap,
                                                   tip='Colormap.')
        self.place_object(self.comboxBox_colormap, row=0, column=0)
        self.connect(self.comboxBox_colormap.signal_changed, self.comboxBox_colormap_changed)

        # Place a save button
        self.button_save = egg.gui.Button('Save :)')
        self.place_object(self.button_save, row=0, column=1)
        self.connect(self.button_save.signal_clicked, self.button_save_clicked)

        # Place a load button
        self.button_load = egg.gui.Button('Load :3')
        self.place_object(self.button_load, row=0, column=2)
        self.connect(self.button_load.signal_clicked, self.button_load_clicked)    
        
        # Place a checkbox for setting the aspect ratio
        self.checkBox_ratio = egg.gui.CheckBox('Equal Ratio')
        self.place_object(self.checkBox_ratio, row=0, column=3)
        self.connect(self.checkBox_ratio.signal_changed, self.checkBox_ratio_changed)
        
        # A plot item for showing the incoming data
        self.plot_item = egg.pyqtgraph.PlotItem()
        self.plot_image = egg.pyqtgraph.ImageView(view=self.plot_item)
        self.place_object(self.plot_image,row=1, column=0,column_span=4, alignment=0)  
        
        # Strectch
        self.set_column_stretch(3)
        
        
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
        
        # Initiate the gui with the values of the widgets
        self.comboxBox_colormap_changed()
        self.checkBox_ratio_changed()
        
    def comboxBox_colormap_changed(self):
        """
        Called when the combo box changes
        """
        self.color_name = self.comboxBox_colormap.get_text()
        _debug('map2D: comboxBox_colormap_changed ', self.color_name)
        
        mycmap = self.colormaps.get_colormap(self.color_name)
        self.plot_image.setColorMap(mycmap)
    
    def checkBox_ratio_changed(self):
        """
        Set or remove the ratio to be equal
        """
        _debug('map2D: checkBox_ratio_changed')
        
        # Set the ratio according to the wishes
        value = self.checkBox_ratio.is_checked()
        self.plot_image.view.setAspectLocked(value) # Input True for having the scaling right.         
        

    def button_save_clicked(self):
        """
        Save the data shown.
        """                       
        _debug('map2D: button_save_clicked')
        
        self.databox = sm.data.databox()
        
        # Put nice headers
        self.databox.insert_header('xmin'  , self.xmin)
        self.databox.insert_header('xmax'  , self.xmax)
        self.databox.insert_header('Nx'    , self.Nx)
        self.databox.insert_header('labelX', self.labelX)
        self.databox.insert_header('ymin'  , self.ymin)
        self.databox.insert_header('ymax'  , self.ymax)
        self.databox.insert_header('Ny'    , self.Ny)
        self.databox.insert_header('labelY', self.labelY)
        N_col = len(self.Z) # Number of columns
        self.databox.insert_header('N_columns', N_col)
        
        # Put the columns :D 
        for i in range(N_col):
            col = self.Z[i]
            self.databox['column_%d'%i] = col            
            
        # This will open a dialog window for saving the databox
        self.databox.save_file()
        

    def button_load_clicked(self):
        """
        Load scans. 
        It load what is saved with the complement method "button_save_clicked".
        
        """                       
        _debug('map2D: button_load_clicked')
        
        # Get the databox
        self.databox = sm.data.load(text='Select Scan')
        
        
        # Load the image
        Nx     = self.databox.headers['Nx']
        Ny     = self.databox.headers['Ny']
        Z = np.zeros([Ny, Nx])
        # Add each column 
        for i in range(Ny):
            Z[i] = self.databox['column_%d'%i]    
            
        
        self.set_data(Z, 
                      x_info=(self.databox.headers['xmin'],
                              self.databox.headers['xmax'],
                              self.databox.headers['Nx']),
                      y_info=(self.databox.headers['ymin'],
                              self.databox.headers['ymax'],
                              self.databox.headers['Ny']),
                      label_x=self.databox.headers['labelX'], 
                      label_y=self.databox.headers['labelY'])
        
    def set_data(self, Z, 
                 x_info=-1, y_info=-1,
                 label_x=-1, label_y=-1):
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
                   
        # Update the image
        self.plot_image.setImage(self.Z.T,
                                 pos=(self.posX, self.posY),
                                 scale =(self.scaleX, self.scaleY))      
        # scale/pan the view to fit the image.
        self.plot_image.autoRange()

        
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
                               'ca_va_bien_aller',
                               'gotta_catch_em_all']
        
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
        if name =='gotta_catch_em_all':
            return self.gotta_catch_em_all()
        
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

    def gotta_catch_em_all(self):
        """
        Dark blue to dark red. Passing trough yellow. 
        Like the first set of pokemon game !
        """
        
        colors = [
                (0, 0, 100),
                (0, 0, 255),
                (0, 255, 255),
                (255, 255, 0),
                (255, 0, 0),
                (100, 0, 0)]
        
        return egg.pyqtgraph.colormap.ColorMap(pos=np.linspace(0.0, 1.0, len(colors)), color=colors)  
        
        
if __name__ == '__main__':
    _debug_enabled     = True
    
    

    

    
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
    
    # Initiate the mapper
    self = map2D()
    self.show()
    self.set_data(Z, (x.min(), x.max(), len(x)), (y.min(), y.max(), len(y)),
                  'Hey x', 'Holla y')
    
    # Just verify the list of colormap. 
    list_color = self.colormaps.get_list_colormaps()
    print('List of colormap = ', list_color)    
    
    
#     # Try some other data
#    ts = np.linspace(5, 20, 1000)
#    
#    x = np.linspace(-20, 20, 200)
#    y = np.linspace(-20, 20, 200)
#    X,Y = np.meshgrid(x,y)
#    
#    Gauss = 0
#    for t in ts:
#        x1 = 2*t*np.cos(t)*np.sin(0.5*t)  
#        y1 = 4*t*np.sin(t)*np.sin(0.25*t)      
#        Gauss_t = np.exp(-( (X-x1)**2+(Y-y1)**2 )/4)
#        Gauss += Gauss_t
#        
#    Z = Gauss
#    
#    # Initiate the mapper
#    self = map2D()
#    self.show()
#    self.set_data(Z, (x.min(), x.max(), len(x)), (y.min(), y.max(), len(y)),
#                  'Hey x', 'Holla y')   
#    
#    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    