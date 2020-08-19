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
        

class GUIAdaptiveT1Bayes(egg.gui.Window):
    """
    GUI for managing the adaptive protocole for T1 measurement. Using 
    Bayesian inference to adapt the best time to probe. 
    """   
    
    def __init__(self, gui_pulser, name="Super adaptive Bayes Bad Ass", size=[1000,500]): 
        """
        Initialize
        
        gui_pulser:
            Object GuiMainPulseSequence in gui_pulser. 
            This will allow to control the pulse sequence. 
        """    
        _debug('GUIAdaptiveT1Bayes: __init__')
        _debug('Oh yes, the past can hurt. But the way I see it, you can either run from it or learn from it. – The Lion King')
        
        # Run the basic stuff for the initialization
        egg.gui.Window.__init__(self, title=name, size=size)
        
        # Initialise the GUI
        self.initialize_GUI()
        

    def button_run_clicked(self):
        """
        Run the protocole !
        """
        _debug('GUIAdaptiveT1Bayes: button_run_clicked')
        
        # Make the attribute to match with the settings
        self.initiate_attributes()
        
    def button_save_clicked(self):
        """
        Save everything !
        """
        _debug('GUIAdaptiveT1Bayes: button_save_clicked')
        print('Implement me !!')
        
        
    def initialize_GUI(self):
        """
        Fill up the GUI
        """      
        _debug('GUIAdaptiveT1Bayes: initialize_GUI')

        # A button for preparing stuff
        self.button_run = egg.gui.Button('Start', tip='Launch the experiment')
        self.button_run.set_style('background-color: rgb(0, 200, 0);')
        self.place_object(self.button_run, row=0, column=0)
        self.connect(self.button_run.signal_clicked, self.button_run_clicked)

        # Place a buttong for saving the data
        self.button_save = self.place_object(egg.gui.Button(), row=0, column=1,
                                             alignment=1)
        self.button_save.set_text('Save :D :D :D')
        self.connect(self.button_save.signal_clicked, self.button_save_clicked)  
        
        # tree dictionnarry for the settings
        self.treeDic_settings = egg.gui.TreeDictionary(autosettings_path='setting_adaptiveT1Bayes')
        self.place_object(self.treeDic_settings, row=1, column=0)
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
        self.place_object(self.plot_image, row=1, column = 1, 
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
    


class Bayes3Measure():
    """
    Bayes inference for 3 measure
    
    Take the data and update the posterior
     
    """

    def __init__(self, model_functions, constants):
        """
        model_functions = [f0, fp, fm]
        constants = [PL0, contrast]
        
        f0,fp,fm:
            Function with signature (t,Gp,Gm) which gonna define the PL for the 
            three type of measurement. Those are amoung the 9 in the model. 

        PL0:
            Mean photocounts from the ms=0 state. 
        contrast:
            Contrast in photoluminescence from the ms=+-1 state. This is 
            defined such that the photoluminescence coming from ms=+-1 is 
            PL0*(1-contrast)     
            
        """
        _debug('Bayes3Measure: __init__')
        _debug('Your limitation-it’s only your imagination.')
       
        self.model_functions = model_functions        
        self.f0 = model_functions[0]
        self.fp = model_functions[1]
        self.fm = model_functions[2]
        
        # For now the constants are just used for taking measurement, because
        # they are not taken into account 
        self.constants = constants
        
    def update_post(self):
        """
        Update the posterior. 
        Compute it from the like-lihood and the prior, than normalize it
        """
        _debug('Bayes3Measure: update_post' )
            
        #Get the posterior from the like-lihood and the prior
        self.Ppost  = np.exp(-self.L)*self.prior
        self.Ppost /= self.integral2D(self.gp_axis, self.gm_axis, self.Ppost) #Normalize 
        if _debug_enabled:
            #Put this debug into an extra of, because the extra calculation of the volume might be expensive 
            _debug('Volume of posterior (its not fun)  = ', self.integral2D(self.gp_axis, self.gm_axis, self.Ppost ) )    

    def get_likelihood(self, exp0, expp, expm, diffp, diffm):   
        """
        Update the likehihood, from the knowledge of the cumulated measurement
        
        exp0:
            Expectation array for f0. The array is for each element of the domain. 
        expp:
            Expectation array for fp. The array is for each element of the domain. 
        expm:
            Expectation array for fm. The array is for each element of the domain.   
            
            
            
        """
        _debug('Bayes3Measure: get_likelihood_3measure')
        
        # Precompute arrays for simplification
        ZZZ = expp*expm +exp0*(expp+expm)
        
        A = (exp0 + expp + expm +2*(diffp+diffm) 
            + diffp*diffp/expp + diffm*diffm/expm )
        
        B = (expp*diffm + expm*(3*expp+diffp))**2       
        C = exp0/(expp*expm*ZZZ)
        # THE like-lihood
        L = 0.5*(np.log(ZZZ) + A - B*C )
        
        return L     



    
if __name__=="__main__":
    _debug_enabled = True
    
     # Create the fpga api
    bitfile_path = ("X:\DiamondCloud\Magnetometry\Acquisition\FPGA\Magnetometry Control\FPGA Bitfiles"
                    "\Pulsepattern(bet_FPGATarget_FPGAFULLV2_WZPA4vla3fk.lvbitx")
    resource_num = "RIO0"     
    
    import fpga_control as _fc
    fpga_fake = _fc.FPGA_fake_api(bitfile_path, resource_num) # Create the api   
    fpga_fake.open_session()
    
    import gui_pulser
    gui = gui_pulser.GuiMainPulseSequence(fpga_fake)
    
    
    self = GUIAdaptiveT1Bayes(gui)
    self.show()
    
    
    
    
    