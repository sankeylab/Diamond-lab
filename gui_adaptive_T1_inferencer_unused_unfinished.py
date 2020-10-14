# -*- coding: utf-8 -*-
"""
Created on Thu Oct  8 11:39:41 2020

Goal: define the measurer for the adaptive protocole of T1

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






class GUIBayesInference(egg.gui.Window):
    """
    GUI for calculating and showing the PDF of the two rates of the two rates.
    """   
    
    def __init__(self, bayes_inferencer, name="Bayes inference T1", size=[1000,500]): 
        """
        
        bayes_inferencer:
            Object from the script "Bayes_rates" which do all the bayes 
            computation. It is an imput because this GUI is meant to be part 
            of an adaptive protocol that gonna contain the Bayes measurement. 
        
        """    
        _debug('GUIBayesInference:__init__')
        _debug('You can control two things: your work ethic and your attitude about anything. – Ali Krieger')
        
        # Run the basic stuff for the initialization
        egg.gui.Window.__init__(self, title=name, size=size)
        

        # Steal the pulser, mouhahaha
        self.bayes_inferencer  = bayes_inferencer
        
        # Initialise the GUI
        self.initialize_GUI()
        
    def initialize_GUI(self):
        """
        Fill up the GUI
        """        
        _debug('GUIBayesInference: initialize_GUI')

        # A button for initiating the 
        self.button_dummy = egg.gui.Button('Start', tip='Launch the experiment')
        self.button_run.set_style('background-color: rgb(0, 200, 0);')
        self.place_object(self.button_dummy, row=0, column=0)
        
        
        # Add the map for the posterior
        self.map_post = gui_map_2D.map2D()
        self.place_object(self.map_post, row=1)
        
        

        
     
        
if __name__=="__main__":
    # Test the object
    
    _debug_enabled = True
    
    import Bayes_rates
    bayes = Bayes_rates.Bayes()

    # Test the Bayes class with a measurement of thetwo type of difference 
    # Define the grid for th rates
    Gp_min = 0.001*1e3   #Minimum guess for gamma plus (Hz) 
    Gp_max = 107*1e3  #Maximun guess for gamma plus (Hz)        
    Gm_min = 0.001*1e3   #Minimum guess for gamma minus (Hz) 
    Gm_max = 106*1e3  #Maximun guess for gamma minus (Hz)  
    #Define the domain      
    gp_axis = np.linspace(Gp_min, Gp_max, 203) 
    gm_axis = np.linspace(Gm_min, Gm_max, 301) 
    mesh_gp, mesh_gm = np.meshgrid(gp_axis, gm_axis)
    #Define the prior 
    prior = 1+np.zeros([len(gm_axis), len(gp_axis)])  
    
    # Initiate the GUI
    self = GUIBayesInference(bayes)
    self.show()            
        
    # The the methods. 
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
