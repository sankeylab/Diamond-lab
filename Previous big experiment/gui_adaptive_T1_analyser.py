# -*- coding: utf-8 -*-
"""
Created on Thu Oct  8 11:39:41 2020

Goal: A gui to analyse the posterior PDF

@author: Childresslab
"""


import gui_map_2D 

import numpy as np
from spinmob import egg
import traceback
_p = traceback.print_last #Very usefull command to use for getting the last-not-printed error


_debug_enabled     = False
def _debug(*a):
    if _debug_enabled: 
        s = []
        for x in a: s.append(str(x))
        print(', '.join(s))





def integral_2D(x,y, Z):
    """
    Integrate in 2 dimension Z. 
    Z is the 2D array to integrate. 
    x and y are both 1D array used to define the axis of Z
    """
    _debug('integral2D')
    
    firstInt = np.trapz(Z, x=x, axis=1) #First integrate along the first axis
    return     np.trapz(firstInt, x=y) #Integrate over the remaining axis

def means_2D(x,y, prob):
    """
    Compute the means of xs and ys according to the probability density 
    function prob
    
    x and y:
        Both 1D array used to define the axis of prob
        
    prob:
        2D array to integrate. 
    """
    _debug('means_2D')
    
    mesh_x, mesh_y = np.meshgrid(x,y)
    
    # Compute the mean of each axis
    mean_x = integral_2D(x, y, prob*mesh_x)
    mean_y = integral_2D(x, y, prob*mesh_y)
    
    return mean_x, mean_y


class GUIBayesAnalyser(egg.gui.Window):
    """
    GUI for analysing the posterior PDF and take decision.
    """   
    
    def __init__(self, name="Bayes inference T1", size=[1000,500]): 
        """
        
        """    
        _debug('GUIBayesAnalyser:__init__')
        _debug('You can control two things: your work ethic and your attitude about anything. – Ali Krieger')
        
        # Run the basic stuff for the initialization
        egg.gui.Window.__init__(self, title=name, size=size)
        
        # Initiate the attribute
        self.best_gp, self.best_gm     = (0, 0) # Best estimate of the rate so far
        self.t_probe_p, self.t_probe_m = (0, 0) # Best time to probe for each measurement
        
        
        # Initialise the GUI
        self.initialize_GUI()
        
    def initialize_GUI(self):
        """
        Fill up the GUI
        """        
        _debug('GUIBayesAnalyser: initialize_GUI')

        # tree dictionnarry for the settings
        self.treeDic_settings = egg.gui.TreeDictionary(autosettings_path='setting_adaptiveT1Bayes_analyser')
        self.place_object(self.treeDic_settings, row=0, column=0)
        
        # Add parameters
        self.list_method = ['Mean_rate', 'Minimize_sensitivity']
        self.treeDic_settings.add_parameter('Decision_method', self.list_method, 
                                            tip='Which method to use for deciding the next time to probe')
        
        self.list_type_of_measurement = ['diffp', 'diffm']
        self.treeDic_settings.add_parameter('Type_of_measurement', self.list_type_of_measurement, 
                                            tip='What type of measurement to make.')   
        self.treeDic_settings.add_parameter('N_readout', 3000, 
                                            type='int', step=1, 
                                            bounds=[0,None],
                                            tip='Number of readout before re-adapting')  
                
        
        # Add a label for showing some results
        # Make a label for showing some estimate
        txt = ('Best rates so far: Gp = xxx kHz  Gm = xxx kHz')
        self.label_info = egg.gui.Label(txt)
        self.place_object(self.label_info, row=0, column=2)   
        self.label_info_update() # Update it
        
    def label_info_update(self):
        """
        Update the information shown on the label
        """
        _debug('GUIBayesAnalyser: label_info_update')
        
        txt = ('Best rates so far: Gp = %f kHz  Gm = %f kHz'%(self.best_gp*1e-3,
                                                              self.best_gm*1e-3)
            +'\nTime to probe: tp = %f us  tm = %f us'%(self.t_probe_p*1e6, self.t_probe_m*1e6))
            
        self.label_info.set_text(txt)
        
        
    def determine_time_to_probe(self, gp_axis, gm_axis, post):
        """
        Determine the best time to probe from the posterior PDF. 
        
        gp_axis:
            (1D numpy array) axis of gamma+ in the pdf
        gm_axis:
            (1D numpy array) axis of gamma- in the pdf
        post:
            (2D numpy array) Posterior pdf
            
        """
        _debug('GUIBayesAnalyser: determine_time_to_probe')
        
        
        # The method depends on the selction
        self.method = self.treeDic_settings['Decision_method']
        if self.method == 'Mean_rate':    
            # Estimate the mean rate
            self.best_gp, self.best_gm = means_2D(gp_axis, gm_axis, post)
            
            # Estimate the two optimal time to probe for each rate
            self.t_probe_p = 0.5/self.best_gp
            self.t_probe_m = 0.5/self.best_gm
            self.label_info_update()
            
        else:
            # There is no other implemented method for now. 
            pass 
        
        return self.t_probe_p, self.t_probe_m

        
     
        
if __name__=="__main__":
    # Test the object
    
    _debug_enabled = True
    
    # Initiate the GUI
    self = GUIBayesAnalyser()
    self.show()            
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
