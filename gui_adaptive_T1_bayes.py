# -*- coding: utf-8 -*-
"""
Created on Mon Aug 17 16:34:14 2020

@author: Childresslab
"""

import numpy as np
from spinmob import egg
import traceback
_p = traceback.print_last #Very usefull command to use for getting the last-not-printed error

# For adaptive protocols
import protocol_model
import protocol_bayes


_debug_enabled     = False

def _debug(*a):
    if _debug_enabled: 
        s = []
        for x in a: s.append(str(x))
        print(', '.join(s))
        

class GUIT1probeOneTime(egg.gui.Window):
    """
    GUI for preparing the states and let them decay until a single time.
    """   
    
    def __init__(self, name="Single probe T1", size=[1000,500]): 
        """
        Initialize
        """    
        _debug('GUIAdaptiveT1Bayes: __init__')
        _debug('Oh yes, the past can hurt. But the way I see it, you can either run from it or learn from it. – The Lion King')
        
        # Run the basic stuff for the initialization
        egg.gui.Window.__init__(self, title=name, size=size)
        
        # Initialise the GUI
        self.initialize_GUI()
        
    def initialize_GUI(self):
        """
        Fill up the GUI
        """      
        _debug('GUIAdaptiveT1Bayes: initialize_GUI')
        
        # tree dictionnarry for the settings
        self.treeDic_settings = egg.gui.TreeDictionary(autosettings_path='setting_T1_singleTime')
        self.place_object(self.treeDic_settings, row=2, column=0)
        self.treeDic_settings.add_parameter('Rate_+_min', 0.01, 
                                            type='float', step=0.1, 
                                            bounds=[0,None], suffix=' Hz',
                                            tip='Guess for the minimum value of the rate gamma+') 
        self.treeDic_settings.add_parameter('Rate_+_max', 150*1e3, 
                                            type='float', step=0.1, 
                                            bounds=[0,None], suffix=' Hz',
                                            tip='Guess for the maximum value of the rate gamma+') 
        self.treeDic_settings.add_parameter('Size_rate_+_axis', 150, 
                                            type='int', step=10, 
                                            bounds=[0,None],
                                            tip='Number of points along the gamma+ axis for the pdf') 
        self.treeDic_settings.add_parameter('Rate_-_min', 0.01, 
                                            type='float', step=0.1, 
                                            bounds=[0,None], suffix=' Hz',
                                            tip='Guess for the minimum value of the rate gamma-')         
        self.treeDic_settings.add_parameter('Rate_-_max', 150*1e3, 
                                            type='float', step=0.1, 
                                            bounds=[0,None], suffix=' Hz',
                                            tip='Guess for the maximum value of the rate gamma-')
        self.treeDic_settings.add_parameter('Size_rate_-_axis', 150, 
                                            type='int', step=10, 
                                            bounds=[0,None],
                                            tip='Number of points along the gamma- axis for the pdf') 
        self.list_prior_types = ['Flat', 'Gaussian']
        self.treeDic_settings.add_parameter('Prior_type', self.list_prior_types, 
                                            tip='Which prior to use. Based on the bounds given for the rates.')  


        self.treeDic_settings.add_parameter('PL0', 0.04, 
                                            type='float', step=0.04, 
                                            bounds=[0,None], 
                                            tip='Mean photocounts from ms=0 for a SINGLE readout') 
        self.treeDic_settings.add_parameter('Contrast', 0.1, 
                                            type='float', step=0.01, 
                                            bounds=[0,None], 
                                            tip='Contrast between the state ms=0 and ms=+-1 at time=0.\nThis is defined as (PL0-PL+-)/PL0, where PL+- is the mean photocount of ms=+-1.') 
 
        # Add the Image View for the posterior. 
        self.plot_item = egg.pyqtgraph.PlotItem()
        # Put an image in the plot item. 
        self.plot_image = egg.pyqtgraph.ImageView(view=self.plot_item)
        self.place_object(self.plot_image, row=2, column = 1, 
                          row_span=2, column_span=3, alignment=0)  
        self.set_column_stretch(1,10)
        self.set_row_stretch(1,10)
        
        # Add a dummy map 
        x = np.linspace(1, 20, 100)
        y = np.linspace(1, 20, 100)
        X,Y = np.meshgrid(x,y)


    def initiate_attributes(self):
        """
        Initiate the attribute from the parameter choosen. 
        Prepare the prior based on the parameters choosen. 
        """
        _debug('GUIAdaptiveT1Bayes: initiate_attributes') 
        
        # Set the prior
        # Extract the bounds
        self.Gp_min       = self.treeDic_settings['Rate_+_min']   #Minimum guess for gamma plus (Hz) 
        self.Gp_max       = self.treeDic_settings['Rate_+_max']  #Maximun guess for gamma plus (Hz)    
        self.size_axis_Gp = self.treeDic_settings['Size_rate_+_axis'] # Size of the axis gamam plus
        self.Gm_min       = self.treeDic_settings['Rate_-_min']   #Minimum guess for gamma minus (Hz) 
        self.Gm_max       = self.treeDic_settings['Rate_-_max']  #Maximun guess for gamma minus (Hz)  
        self.size_axis_Gm = self.treeDic_settings['Size_rate_-_axis'] # Size of the axis gamam minus
        #Define the axis for the prior pdf      
        self.gp_axis = np.linspace(self.Gp_min, self.Gp_max, self.size_axis_Gp) 
        self.gm_axis = np.linspace(self.Gm_min,self. Gm_max, self.size_axis_Gm) 
        # Set the prior according to the type of prior
        if self.treeDic_settings['Prior_type'] == 'Flat':
            #Define the prior 
            self.prior = 1+np.zeros([len(self.gm_axis), len(self.gp_axis)])      
            # No need to normalize it for now. 
        if self.treeDic_settings['Prior_type'] == 'Gaussian':
            # The priore will be gaussian, with the widtdt set by the bounds
            X,Y = np.meshgrid(self.gp_axis,self.gm_axis)
            x0 = np.mean(self.gp_axis)
            y0 = np.mean(self.gm_axis)
            dx = 0.5*(self.Gp_max-self.Gp_min) # Width in the gamma+ direction
            dy = 0.5*(self.Gm_max-self.Gm_min) # Width in the gamma- direction
            self.prior = np.exp(-( (X-x0)*(X-x0)/dx**2 + (Y-y0)*(Y-y0)/dy**2 )) # A non-skewed gaussian

        # Initiate the class for processing the protocol
        # Define the constants
        self.PL0      = self.treeDic_settings['PL0']
        self.contrast = self.treeDic_settings['Contrast']
        constants = [self.PL0, self.contrast]
        # Define the model functions that should describe our experiment. 
        #TODO Have these models as an input and prepare the pulse sequence accordingly.
        f0 = protocol_model.PLModel(constants).PL00
        fp = protocol_model.PLModel(constants).PLp0
        fm = protocol_model.PLModel(constants).PLm0
        model_functions = [f0, fp, fm]
            
        # Initiate the class. This class will contain the posterior and everything else. 
        self.protocol_processor = protocol_bayes.Bayes3Measure(model_functions, constants)
        self.protocol_processor.initialize(self.gp_axis, self.gm_axis, self.prior)
        
        # Adjust the informaton
        self.update_information()

    def update_information(self):
        """
        Update the information from the object
        """
        _debug('GUIAdaptiveT1Bayes: update_information')
        # Extract the information so far
        self.t_probe   = self.protocol_processor.get_t_probe()
        self.gp_axis   = self.protocol_processor.get_gp_axis()
        self.gm_axis   = self.protocol_processor.get_gm_axis()
        self.posterior = self.protocol_processor.get_posterior()
        
        #TODO Define "get" methods for that. Or just keep it as it is ;p
        self.Gp_guess = self.protocol_processor.Gp_guess
        self.Gm_guess = self.protocol_processor.Gm_guess
        self.eGp_guess = self.protocol_processor.eGp_guess
        self.eGm_guess = self.protocol_processor.eGm_guess
        
        
    def update_plot_posterior(self):
        """
        Update the plot of the posterior. The title should be clear lol. 
        """    
        _debug('GUIAdaptiveT1Bayes: update_plot_posterior')
        
 
        # Set the axis 
        # Get the scale (AKA the spacing between two neighboor points on the image)
        self.scale_x = (self.gp_axis.max()-self.gp_axis.min())/len(self.gp_axis)*1e-3
        self.scale_y = (self.gm_axis.max()-self.gm_axis.min())/len(self.gm_axis)*1e-3
        
        self.plot_item.setLabel('bottom', text='Gamma + (kHz)')
        self.plot_item.setLabel('left'  , text='Gamma - (kHz)')      
        
        # Set the image
        self.plot_image.setImage(self.posterior.T,
                                 pos=(self.gp_axis.min(), self.gm_axis.min()),
                                 scale =(self.scale_x, self.scale_y) )
        # magic method for the image to fill all the space
        self.plot_image.view.setAspectLocked(False) # Input True for having the scaling right.              
    
    
    