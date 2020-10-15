# -*- coding: utf-8 -*-
"""
Created on Mon Aug 17 16:34:14 2020

@author: Childresslab
"""

import gui_adaptive_T1_measurer
import gui_adaptive_T1_analyser
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
        
        # Some attributes
        self.t_probe_p, self.t_probe_m = [0, 0] # Best time to probe
        
               
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
        
        # Specific things for the pulse sequence for ms=+1
        self.treeDic_settings.add_parameter('Pipulse+/frequency', 3.1, 
                                            type='float', step=0.1, decimals=10,
                                            bounds=[0,None], suffix=' GHz',
                                            tip='Frequency of the pipulse for initiating the ms=+1 state')
        self.treeDic_settings.add_parameter('Pipulse+/dt', 0.3, 
                                            type='float', step=0.1, decimals=10,
                                            bounds=[0,None], suffix=' us',
                                            tip='Duration of pi pulse for ms=+1(RF)') 
        self.treeDic_settings.add_parameter('Pipulse+/power', -20, 
                                            type='float', step=1, decimals=10,
                                            bounds=[-50,30], suffix=' dBm',
                                            tip='Constant power of the RF for the pipulse of ms=+1')
        self.treeDic_settings.add_parameter('Pipulse+/DIO_modulation', 2, 
                                            type='int', step=1, 
                                            bounds=[0,16],
                                            tip='DIO for modulating the pi pulse of ms=+1. AKA for sending the RF.')  
        
        # Specific things for the pulse sequence for ms=-1
        self.treeDic_settings.add_parameter('Pipulse-/frequency', 2.7, 
                                            type='float', step=0.1, suffix=' GHz',
                                            bounds=[0,None], decimals=10,
                                            tip='Frequency of the pipulse for initiating the ms=-1 state')
        self.treeDic_settings.add_parameter('Pipulse-/dt', 0.3, 
                                            type='float', step=0.1, decimals=10,
                                            bounds=[0,None], suffix=' us',
                                            tip='Duration of pi pulse for ms=-1(RF)') 
        self.treeDic_settings.add_parameter('Pipulse-/power', -20, 
                                            type='float', step=1, decimals=10,
                                            bounds=[-50,30], suffix=' dBm',
                                            tip='Constant power of the RF for the pipulse of ms=-1')
        self.treeDic_settings.add_parameter('Pipulse-/DIO_modulation', 4, 
                                            type='int', step=1, 
                                            bounds=[0,16],
                                            tip='DIO for modulating the pi pulse of ms=-1. AKA for sending the RF.')  
        
        
        

 
        # Add a tab for each step of the protocol
        self.tabs_steps = egg.gui.TabArea(autosettings_path='tabs_adaptiveT1_steps')
        self.place_object(self.tabs_steps,row=1, column=1,
                          column_span=4, alignment=0)
        
        # Tab for the analyser
        self.gui_analyser = gui_adaptive_T1_analyser.GUIBayesAnalyser()
        self.tab_analyser = self.tabs_steps.add_tab('Analyser')
        self.tab_analyser.place_object(self.gui_analyser, 
                                      alignment=0)
        # Tab for the measurer
        self.tab_measurer = self.tabs_steps.add_tab('Measurer')
        self.gui_measurer = gui_adaptive_T1_measurer.GUIProbe2StatesOneTime(self.gui_pulser)
        self.tab_measurer.place_object(self.gui_measurer, 
                                      alignment=0)
        # Tab for the inferencer
        # Add the map for the posterior
        self.map_post = gui_map_2D.map2D()
        self.tab_inferencer = self.tabs_steps.add_tab('Inferencer')
        self.tab_inferencer.place_object(egg.gui.CheckBox('I am doing inference everyday.'), 
                                      row=0, alignment=0)
        self.tab_inferencer.place_object(self.map_post, 
                                         row=1, column=0, alignment=0)
        
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

        # Define the constants
        self.PL0      = self.treeDic_settings['PL0']
        self.contrast = self.treeDic_settings['Contrast']
        
        
        # Bayes class
        self.bayes = Bayes_rates.Bayes()
        self.bayes.initiate(self.prior, self.mesh_gp, self.mesh_gm)
        
        # Update the map of the posterior
        self.update_map_post()
        

        
        
        
        
        
    def update_map_post(self):
        """
        Make the map of the posterior of the Bayesinferencer so far
        """
        _debug('GUIManager: update_map_post')
        # Put the posterior
        self.map_post.set_data(self.bayes.post, # Z
                               (self.Gp_min*1e-3, self.Gp_max*1e-3 , self.size_axis_Gp), # (xmin, xmax), size(x)
                               (self.Gm_min*1e-3, self.Gm_max*1e-3 , self.size_axis_Gm), # (ymin, ymax), size(y)
                               'Gamma + (kHz)', 'Gamma - (kHz)')
    def step1_adapt_parameters(self):
        """
        Adapt the set of parameters for the next measurement. 
        It take the information from the posterior of the Bayes inference. 
        """
        _debug('GUIManager: step1_adapt_parameters')
        
        # Get the best time to probe
        res = self.gui_analyser.determine_time_to_probe(self.gp_axis, 
                                          self.gm_axis, 
                                          self.bayes.post)   
        self.t_probe_p, self.t_probe_m = res
        
        # Adapt the parameters of the pulse sequence according to the type of measurement
        self.type_of_measurement = self.gui_analyser.treeDic_settings['Type_of_measurement']
        # Set the parameters of the pulse sequence 
        if self.type_of_measurement == 'diffm':
            # Adapt the parameters of the pulse sequence
            # The time probed is the best time for the diffm
            self.t_probe = self.t_probe_m
            # The pipulse is the pi-pulse for ms=-
            p   = self.treeDic_settings['Pipulse-/power']
            f   = self.treeDic_settings['Pipulse-/frequency']
            dt  = self.treeDic_settings['Pipulse-/dt']
            DIO = self.treeDic_settings['Pipulse-/DIO_modulation']
            
        if self.type_of_measurement == 'diffp':
            # Adapt the parameters of the pulse sequence
            # The time probed is the best time for the diffm
            self.t_probe = self.t_probe_p
            # The pipulse is the pi-pulse for ms=-
            p   = self.treeDic_settings['Pipulse+/power']
            f   = self.treeDic_settings['Pipulse+/frequency']
            dt  = self.treeDic_settings['Pipulse+/dt']
            DIO = self.treeDic_settings['Pipulse+/DIO_modulation']                                                    
            
        # Set the parameters of the pulse sequence
        self.gui_measurer.treeDic_settings['t_probe'] = self.t_probe
        self.gui_measurer.treeDic_settings['Frequency'] = f
        self.gui_measurer.treeDic_settings['Power']     = p
        self.gui_measurer.treeDic_settings['dt_pi_pulse'] = dt
        self.gui_measurer.treeDic_settings['DIO_pulse_modulation'] = DIO
        
        
        # Determine the number of readout for the next measurement. 
        self.N_readout = self.gui_analyser.treeDic_settings['N_readout']
        # We roughly want the loop to last less than one second. This is in
        # order to avoid freeze out of the GUI
        self.N_readout_per_FPGA_loop = int(1/(10*self.t_probe)) 
        # Determine how many FPGA loop to perfom. 
        # We take the ceil, such that we have at least 1 loop. 
        self.N_FPGA_loop = int( np.ceil(self.N_readout/self.N_readout_per_loop) )
        
        
    def step2_run_measurement(self):
        """
        Perform a measurement at the time probed.
        
        """
        _debug('GUIManager: step2_run_measurement')
        
        # Prepare the parameters of the pulse sequence
        # It gonna depends on what type of measurement
        
        
        
        # Prepare the pulse sequence
        self.gui_measurer.button_prepare_experiment.click()
        
        # Convert the pulse sequence
        self.gui_pulser.button_convert_sequence.click()
        
        # Set the number of readout
        #TODO re-organize all the pulse sequence for making this step less clumpsy
        self.gui_pulser.gui_pulse_builder.NumberBox_repetition.set_value(self.N_readout_per_FPGA_loop) 
        # Set the number of FPGA loop to have. 
        self.gui_pulser.NumberBox_N_loopFPGA.set_value(self.N_FPGA_loop)
        
        # Run it !
        # It should stop after that the number of FPGA loop is performed
        print('Measurerment started')
        self.gui_pulser.button_start.click()
        print('Measurerment done!')        
        
    def step3_extract_measurement(self):
        """
        Extract the data from the measurement taken
        """
        _debug('GUIManager: step3_extract_measurement')
        print('Implement me !')
        
        
        
        
    def button_run_clicked(self):
        """
        Run the protocole !
        """
        _debug('GUIManager: button_run_clicked')
        
        # Make the attribute to match with the settings
        self.initiate_attributes()
        
        # Step 1: Analyse the posterior to determine the best time to probe
        # We gonna adapt all the parameters 
        self.step1_adapt_parameters()
        
        # Step 2: Take a measurement with that.
        self.step2_run_measurement()
        
        # Step 3: Feed the measurement data to the bayes inferencer
        self.step3_extract_measurement()
        # EX: self.bayes.give_measurement_diffp(arguments)


    def button_save_clicked(self):
        """
        Save everything !
        """
        _debug('GUIManager: button_save_clicked')
        print('Implement me !!')
        # Note: we mght want to save everything in every GUI. 
        # That might require many databox. 


    
if __name__=="__main__":
    _debug_enabled = True
    gui_adaptive_T1_measurer._debug_enabled = True
    gui_adaptive_T1_analyser._debug_enabled = True
    
    # Get the fpga paths and ressource number
    import spinmob as sm
    infos = sm.data.load('cpu_specifics.dat')
    bitfile_path = infos.headers['FPGA_bitfile_path']
    resource_num = infos.headers['FPGA_resource_number']
    
#    # Get the fpga API
#    import api_fpga as _fc
#    fpga = _fc.FPGA_api(bitfile_path, resource_num) 
#    fpga.open_session()
#    
#    import gui_pulser
#    # Note: we could also feed the pulser with the optimizer, but it is mostly
#    # in the main experiment GUI that it matters. 
#    gui = gui_pulser.GuiMainPulseSequence(fpga)
#    gui.show()
#    
#    self = GUIManager(gui, size=[1800,1000])
#    self.show()
#    
    
    
    # For if we want to use the fake API for quick test
    import api_fpga as _fc
    fpga_fake = _fc.FPGA_fake_api(bitfile_path, resource_num) # Create the api   
    fpga_fake.open_session()
    import gui_pulser
    # Note: we could also feed the pulser with the optimizer, but it is mostly
    # in the main experiment GUI that it matters. 
    gui = gui_pulser.GuiMainPulseSequence(fpga_fake)
    gui.show()
    self = GUIManager(gui, size=[1800,1000])
    self.show()
    
    

    
    
    
    
    
    
    
    
    
    
    
    
    