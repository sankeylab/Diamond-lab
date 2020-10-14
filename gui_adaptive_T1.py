# -*- coding: utf-8 -*-
"""
Created on Mon Aug 17 16:34:14 2020

@author: Childresslab
"""

import gui_adaptive_T1_measurer
import gui_map_2D
import Bayes_rates

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


class GUIManager(egg.gui.Window):
    """
    GUI for managing the adaptive protocole for T1 measurement. 
    This gui is the head of the protocol:
        - It Run the measurement
        - It send the data to the Bayes inferecencer
        - It determine the best set of parameters for the next measurement. 
    
    """   
    
    def __init__(self, gui_pulser,  name="Super adaptive T1 Bad Ass", size=[1000,500]): 
        """
        Initialize
        
        gui_pulser:
            Object GuiMainPulseSequence in gui_pulser. 
            This will allow to control the pulse sequence withing the main
            experiment GUI.
            
        """    
        _debug('GUIManager: __init__')
        _debug('Oh yes, the past can hurt. But the way I see it, you can either run from it or learn from it. – The Lion King')
        
        # Run the basic stuff for the initialization
        egg.gui.Window.__init__(self, title=name, size=size)
        
        # Steal the pulser, mouhahaha
        self.gui_pulser = gui_pulser
        
        # Initialise the GUI widgets. 
        self.initialize_GUI()
        
        
               
    def initialize_GUI(self):
        """
        Fill up the GUI
        """      
        _debug('GUIManager: initialize_GUI')

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

        # FOr now we give these value. 
        # We might atsome point just give the prior on them. 
        self.treeDic_settings.add_parameter('PL0', 0.04, 
                                            type='float', step=0.04, 
                                            bounds=[0,None], 
                                            tip='Mean photocounts from ms=0 for a SINGLE readout') 
        self.treeDic_settings.add_parameter('Contrast', 0.1, 
                                            type='float', step=0.01, 
                                            bounds=[0,None], 
                                            tip='Contrast between the state ms=0 and ms=+-1 at time=0.\nThis is defined as (PL0-PL+-)/PL0, where PL+- is the mean photocount of ms=+-1.') 
 
        # Add a tab for each step of the protocol
        self.tabs_steps = egg.gui.TabArea(autosettings_path='tabs_adaptiveT1_steps')
        self.place_object(self.tabs_steps,row=1, column=1,
                          column_span=4, alignment=0)
        
        # Tab for the advisor
        self.tab_advisor = self.tabs_steps.add_tab('Advisor')
        self.tab_advisor.place_object(egg.gui.CheckBox('I am an advisor.'), 
                                      alignment=0)
        # Tab for the employee
        #TODO CHange the name "employee" for "measurer".
        self.tab_employee = self.tabs_steps.add_tab('Measurer')
        self.employee = gui_adaptive_T1_measurer.GUIProbe2StatesOneTime(self.gui_pulser)
        self.tab_employee.place_object(self.employee, 
                                      alignment=0)
        # Tab for the inferencer
        # Add the map for the posterior
        self.map_post = gui_map_2D.map2D()
        self.tab_inferencer = self.tabs_steps.add_tab('Inferencer')
        self.tab_inferencer.place_object(egg.gui.CheckBox('I am doing inference everyday.'), 
                                      alignment=0)
        self.tab_inferencer.place_object(self.map_post)
        
        # Add a label for showing the status
        # Make a label for showing some estimate
        txt = ('We have the best T1 management on the market. '+
               '\n Measurer: Probe one time 3 states')
        self.label_status = egg.gui.Label(txt)
        self.place_object(self.label_status, row=2, column=2)                



    def initiate_attributes(self):
        """
        Initiate the attribute from the parameter choosen. 
        Prepare the prior based on the parameters choosen. 
        """
        _debug('GUIManager: initiate_attributes') 
        
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
        self.mesh_gp, self.mesh_gm = np.meshgrid(self.gp_axis, self.gm_axis)
        # Set the prior according to the type of prior
        if self.treeDic_settings['Prior_type'] == 'Flat':
            #Define the prior 
            self.prior = 1+np.zeros([len(self.gm_axis), len(self.gp_axis)])      
            # No need to normalize it for now. 
        if self.treeDic_settings['Prior_type'] == 'Gaussian':
            # The priore will be gaussian, with the widt set by the bounds
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
        
        self.bayes = Bayes_rates.Bayes()
        self.bayes.initiate(self.prior, )



    def button_run_clicked(self):
        """
        Run the protocole !
        """
        _debug('GUIManager: button_run_clicked')
        print('Implement me !!')
        
        # Make the attribute to match with the settings
        self.initiate_attributes()
        
        #TODO It is here that we gonna implement the measurement and update of
        #TODO  the best time to probe. 
        
        # Update the plot
        self.update_image()        

    def button_save_clicked(self):
        """
        Save everything !
        """
        _debug('GUIManager: button_save_clicked')
        print('Implement me !!')
        # Note: we mght want to save everything in every GUI. 
        # That might require many databox. 
        
        
    def button_fake_a_measure_clicked(self):
        """
        Fake a measure with a fake rate
        """
        _debug('GUIManager: button_fake_a_measure_clicked')
        
        # Fake a measurement
        Gp_true, Gm_true = 15000, 32000
        t = self.gui_pulser.gui_T1_probeOneTime.t_probe*1e-6
        nb_readout = self.gui_pulser.rep
        self.measured_f0 = np.random.poisson(nb_readout*self.model_functions[0](t, Gp_true, Gm_true))
        self.measured_fp = np.random.poisson(nb_readout*self.model_functions[1](t, Gp_true, Gm_true))
        self.measured_fm = np.random.poisson(nb_readout*self.model_functions[2](t, Gp_true, Gm_true))
        diffp = self.measured_f0 - self.measured_fp
        diffm = self.measured_f0 - self.measured_fm
        #Add the fake measure as a data
        self.bayes.add_measurement(t, nb_readout, diffp, diffm)
        # Update the plot
        self.update_image()
                
        
        
    def update_image(self):
        """
        Update the plot of the posterior. The title should be clear lol. 
        """    
        _debug('GUIManager: update_image')
        
 
        # Set the axis 
        # Get the scale (AKA the spacing between two neighboor points on the image)
        self.scale_x = (self.gp_axis.max()-self.gp_axis.min())/len(self.gp_axis)*1e-3
        self.scale_y = (self.gm_axis.max()-self.gm_axis.min())/len(self.gm_axis)*1e-3
        
        self.plot_item.setLabel('bottom', text='Gamma + (kHz)')
        self.plot_item.setLabel('left'  , text='Gamma - (kHz)')      
        
        # Set the image
        self.plot_image.setImage(self.bayes.get_post().T,
                                 pos=(self.gp_axis.min(), self.gm_axis.min()),
                                 scale =(self.scale_x, self.scale_y) )
        # magic method for the image to fill all the space
        self.plot_image.view.setAspectLocked(False) # Input True for having the scaling right.              
    





    
if __name__=="__main__":
    _debug_enabled = True
    gui_adaptive_T1_measurer._debug_enabled = True
    
    # Get the fpga paths and ressource number
    import spinmob as sm
    infos = sm.data.load('cpu_specifics.dat')
    bitfile_path = infos.headers['FPGA_bitfile_path']
    resource_num = infos.headers['FPGA_resource_number']
    # Get the fpga API
    import api_fpga as _fc
    fpga = _fc.FPGA_api(bitfile_path, resource_num) 
    fpga.open_session()
    
    # For if we want to use the fake API for quick test
#    import api_fpga as _fc
#    fpga_fake = _fc.FPGA_fake_api(bitfile_path, resource_num) # Create the api   
#    fpga_fake.open_session()
    
#    import gui_pulser
#    # Note: we could also feed the pulser with the optimizer, but it is mostly
#    # in the main experiment GUI that it matters. 
#    gui = gui_pulser.GuiMainPulseSequence(fpga_fake)
#    gui.show()

    import gui_pulser
    # Note: we could also feed the pulser with the optimizer, but it is mostly
    # in the main experiment GUI that it matters. 
    gui = gui_pulser.GuiMainPulseSequence(fpga)
    gui.show()
    
    self = GUIManager(gui, size=[1800,1000])
    self.show()
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    