# -*- coding: utf-8 -*-
"""
Created on Thu May 21 15:27:02 2020

A GUI for playing with the FPGA

@author: Childresslab, Michael
"""

from spinmob import egg
import traceback
_p = traceback.print_last #Very usefull command to use for getting the last-not-printed error

import api_fpga as _fc
from converter import Converter # This convert the sequence object into fpga data
from pulses import GUIPulsePattern
import pulses
from converter import GUIFPGAInstruction

import time


# Debug stuff.
_debug_enabled     = False

def _debug(*a):
    if _debug_enabled: 
        s = []
        for x in a: s.append(str(x))
        print(', '.join(s))
        

class GuiPulseRunner(egg.gui.Window):
    """
    Main GUI for running the FPGA with pulse sequence. 
    """
    def __init__(self, fpga, 
                 name="Best pulser of the world", size=[1400,700]): 
        """
        fpga:
            "FPGA_api" object from api_fpga.py. 
            This is the object shared amoung the GUIs for controlling the fpga. 
            The session of the fpga must already be open. 
        """    
        _debug('GuiPulseRunner:__init__')
        _debug('Don’t watch the clock; do what it does. Keep going. – Sam Levenson')
        
        # Run the basic stuff for the initialization
        egg.gui.Window.__init__(self, title=name, size=size)
        
        # Get the inputs
        self.fpga = fpga           
       
        # Some attribute
        self.is_running = False # Weither or not the pulse sequence is running    

        # Initialize variable
        self.data_array = []
        self.length_data_block_s = []
        self.selected_experiment = 'Predefined' # This tells which experiment is selected
        # Give a simple sequence by default
        self.sequence = pulses.CoolSequence('rabi_fake').get_sequence() 

        # Fill the GUI
        self.initialize_GUI() 
        
        # Reset the data. This also initialise some attributes
        self.reset_data()

    def initialize_GUI(self):
        """
        Fill up the GUI
        """        
        _debug('GuiPulseRunner: initialize_GUI')

        # Place the run button and connect it
        self.button_start = egg.gui.Button('Start',
                                           tip='Start/Pause the fpga sequence.')
        self.place_object(self.button_start)
        self.connect(self.button_start.signal_clicked, self.button_start_clicked)
        self.button_start.disable() # Disable is until data are available

        # Place the button reset and connect it. 
        self.button_reset= egg.gui.Button("Reset :O")
        self.place_object(self.button_reset)
        self.connect(self.button_reset.signal_clicked, self.button_reset_clicked)
        
        # Place the conversion button and connect it
        self.button_convert_sequence = self.place_object(egg.gui.Button("Convert"))
        self.connect(self.button_convert_sequence.signal_clicked, self.button_convert_sequence_clicked)        
 
        # Place the show_fpga_data button and connect it
        self.button_show_fpga_data = self.place_object(egg.gui.Button("Show FPGA data"))
        self.connect(self.button_show_fpga_data.signal_clicked, self.button_show_fpga_data_clicked)   
        
        # Place a label for the FPGA length 
        self.label_data_length = self.place_object(egg.gui.Label('FPGA data length: XX'))
        
        
                # Place the show_sequence button and connect it
        self.button_show_sequence = self.place_object(egg.gui.Button("Show sequence"))
        self.connect(self.button_show_sequence.signal_clicked, self.button_show_sequence_clicked)    
        
        self.new_autorow()
        # Place a qt SpinBox for the number of FPGA loop
        self.place_object(egg.gui.Label('Maximum Nb of \nFPGA loop'))
        self.NumberBox_N_loopFPGA = egg.gui.NumberBox(value=100000, step=1, 
                                                      bounds=(1, None), int=True)
        self.place_object(self.NumberBox_N_loopFPGA, alignment=0)
        
        # Place a label for the number of iteration performed
        self.iteration_label = self.place_object(egg.gui.Label('Iteration of FPGA:XX'))      

        # A spinbox for the number of iteration before optimization
        self.place_object(egg.gui.Label('Number of FPGA loop\nbefore optimization\n0=never optimize'))
        self.NumberBox_Nloop_before_optimize = egg.gui.NumberBox(value=100, step=1, 
                                                      bounds=(0, None), int=True)
        self.place_object(self.NumberBox_Nloop_before_optimize, alignment=0)
        
        self.new_autorow()
        # A button for setting the delays
        self.sequence_has_delay = False # This will be true if the sequence contain delays, false otherwise
        self.button_set_delays = egg.gui.Button('Set the delays', tip='Set/remove the delays into the sequence.\nRemove and set again for updating new values.')
        self.button_set_delays.set_style('background-color: rgb(255, 155, 255);')         
        self.place_object(self.button_set_delays, row=3, column=0)
        self.connect(self.button_set_delays.signal_clicked, self.button_set_delays_clicked)     
        
        # Prepare the list of delays for pulse
        #Place the AOs with tree dictionary
        self.treeDict_delays  = egg.gui.TreeDictionary(autosettings_path='setting_DIOs_delays')
        self.place_object(self.treeDict_delays, 
                          row=4, column=0, column_span=2)   
        for i in range(8):
            # NOTE: I limited up to DIO7, just to have a smaller dictionary tree, but it can go up to DIO15
            key = 'Delay_raise_DIO%d'%i
            self.treeDict_delays.add_parameter(key, 0, 
                                               type='float', step=0.01, 
                                               bounds=[None,None], suffix=' us',
                                               tip='Time delay for the raise time of DIO%d'%i)        
        for i in range(8):
            # NOTE: I limited up to DIO7, just to have a smaller dictionary tree, but it can go up to DIO15
            key = 'Delay_fall_DIO%d'%i
            self.treeDict_delays.add_parameter(key, 0, 
                                               type='float', step=0.01, 
                                               bounds=[None,None], suffix=' us',
                                               tip='Time delay for the fall time of DIO%d'%i)     
        
        # Number box for setting the number of repetition of the sequence
        self.place_object(egg.gui.Label('Repetion of \nsequence')) #Set the label at position (0,0)
        self.NumberBox_repetition = egg.gui.NumberBox(value=1000, step=1, 
                                                      bounds=(0, None), int=True)
        self.place_object(self.NumberBox_repetition, alignment=1)    
        
        # A check box for setting the CET mode
        self.CheckBox_CET_mode = egg.gui.CheckBox('CET mode?')
        self.place_object(self.CheckBox_CET_mode)        



    def button_convert_sequence_clicked(self):
        """
        What to do is the button convert is clicked
        """
        _debug('GuiPulseRunner: button_convert_sequence_clicked')

        if self.is_running == False:
            # Convert the sequence (Obviously)
            self.convert_sequence()            
            # Unablle the run button, because there are now data to be sent
            self.button_start.enable()
            self.button_start.set_text('Run')
            self.button_start.set_colors(background='green')
            
    def button_start_clicked(self):
        """
        What to do when the run instruction button is clicked
        """
        _debug('GuiPulseRunner: button_start_clicked')
        
        if self.is_running == False:
            self.is_running = True
            self.button_start.set_text('Pause')
            self.button_start.set_colors(background='blue')
            self.run_loops()
            
        else:
            # Stop to run if it is running
            self.is_running = False
            if self.is_reseted:
                self.button_start.set_text('Start')
                self.button_start.set_colors(background='green')       
            else:
                self.button_start.set_text('Continue')
                self.button_start.set_colors(background='green')  

    def button_reset_clicked(self):
        """
        Reset the data
        """
        _debug('GuiPulseRunner:  button_reset_clicked')
        
        # Stop to run 
        if self.is_running:
            self.button_start_clicked()
        # Reset
        self.reset_data()
        
        # Reupdate the button, because the if was not met the first time. 
        self.button_start.set_text('Start')
        self.button_start.set_colors(background='green')         
        
    def button_show_sequence_clicked(self):
        """
        Pop up a window for showing the pulse sequence
        """
        _debug('GuiPulseRunner: button_show_sequence_clicked') 
        
        # Show the block
        GUIPulsePattern(self.sequence)  
        
    def button_show_fpga_data_clicked(self):
        """
        Pop up a window showing the pulses from the fpga data
        """
        _debug('GuiPulseRunner: button_show_fpga_data_clicked')
        
        # Show the GUI
        GUIFPGAInstruction(self.data_array,self.rep, self.length_data_block_s,
                           list_DIO_to_show=range(8)) # Only show the 8 first DIO

    def button_set_delays_clicked(self):
        """
        Add the delays in the sequence
        """
        _debug('GUIPulseBuilder: button_set_delays_clicked') 
        
        # Put the delays only if the sequence do not contain them
        if not(self.sequence_has_delay):
            
            # Keepin memory the sequence with no delay
            self.sequence_no_delay = self.sequence
            
            # Extract the raise delays
            delays_raise = []
            DIOs = []
            for i in range(8):
                DIOs.append(i)
                delays_raise.append( self.treeDict_delays['Delay_raise_DIO%d'%i])
            # Set the raise delay
            new_sequence = pulses.add_raise_delays(self.sequence, DIOs, delays_raise)
    
            # Extract the fall delays
            delays_fall = []
            DIOs = []
            for i in range(8):
                DIOs.append(i)
                delays_fall.append( self.treeDict_delays['Delay_fall_DIO%d'%i])
            # Set the fall delay
            new_sequence = pulses.add_fall_delays(new_sequence, DIOs, delays_fall)   
            
            # Set the sequence to be this one
            self.set_sequence(new_sequence)
            # Note that the sequence has delay
            self.sequence_has_delay = True
            
            #Adjust the button 
            self.button_set_delays.set_text('Remove the delays')
            self.button_set_delays.set_style('background-color: rgb(255, 155, 0);')  
        else:
            # Set the sequence with no delay
            self.set_sequence(self.sequence_no_delay)
            # Note that the sequence has NO delay
            self.sequence_has_delay = False
            #Adjust the button 
            self.button_set_delays.set_text('Set the delays')
            self.button_set_delays.set_style('background-color: rgb(255, 155, 255);')              
                    
            
    def set_sequence(self, sequence):
        """
        Give the sequence to the give. 
        It is this sequence that gonna be transfered into fpgd data and THEN 
        repetead. 
        """
        _debug('GuiPulseRunner: set_sequence')
        
        self.sequence = sequence
        
        
            
    def convert_sequence(self):
        """
        Convert the sequence into data array
        """
        _debug('GuiPulseRunner: convert_sequence')
        # Reset the number of iteration
        self.button_reset_clicked()
        
        time_start = time.time()
        # Extract important information from the pulse sequence
        self.rep      = self.NumberBox_repetition.get_value()
        
        # Create the converter and convert
        cc = Converter()
        self.data_array = cc.sequence_to_FPGA(self.sequence, repetition=self.rep)
        time_elapsed = time.time() - time_start
        
        # Note the data lenght
        length = len(self.data_array)
        text = ('FPGA data length: %d'%length+
                '\nTime for conversion: %f sec'%time_elapsed)
        self.label_data_length.set_text(text )
        # Note also the lentght of each block
        self.length_data_block_s = cc.get_length_data_block_s()

    
    def reset_data(self):
        """
        Initialize the data before the run
        """
        _debug('GuiPulseRunner: reset_data')
        
        # Flush the counts (One moment of silence for all the data who disapeared.)
        self.counts_total = 0        
        
        # Reset the number of iterations
        self.iter = -1         
        
        # Update the label for the number of iteration
        self.iteration_label.set_text('Iteration reseted')          
        
        # Note that it is resetted
        self.is_reseted = True
        
    def prepare_THE_run_loop(self):
        """
        Prepare the fpga settings for the run loop. And get the attributes
        """
        _debug('GuiPulseRunner: prepare_THE_run_loop')
        
        # Note the value of the various settings
        self.Nloop_before_optimize = self.NumberBox_Nloop_before_optimize.get_value()
        self.N_loopFPGA = self.NumberBox_N_loopFPGA.get_value()
        
        
        # Send the data_array to the FPGA and prepare it
        # IMPORTANT We are adding 120 ticks (us) off at both end of the total
        # sequence. This is in order to give some extra time to the fpga to 
        # process the fifo or other stuff. 
        self.fpga.prepare_pulse(self.data_array, nb_ticks_off=120) 
        # Specify the counting mode 
        if self.CheckBox_CET_mode.is_checked() == 0:
            self.fpga.set_counting_mode(False)
        else:
            self.fpga.set_counting_mode(True)
                
    
    def run_loops(self):
        """
        Perform the loops of the fpga has long as the conditions are met. 
        """
        _debug('GuiPulseRunner: run_loops')
        # Rewrite the data in the FPGA, in case they were changed by an other 
        # gui (example: the optimizer between loops)
        self.prepare_THE_run_loop()

        condition_loop = True
        while condition_loop:
            _debug('GuiPulseRunner: run_loops: BEFORE self.iter, self.N_loopFPGA, self.is_running, condition_loop',
                   self.iter,self.N_loopFPGA, self.is_running, condition_loop)
            
            self.iter += 1
            # Update the label for the number of iteration
            self.iteration_label.set_text('Iteration %d'%self.iter)
            _debug('GuiPulseRunner: run_loops %d/%d'%(self.iter, self.N_loopFPGA))
            self.fpga.run_pulse() 

            # Allow the GUI to update. This is important to avoid freezing of the GUI inside loops
            self.process_events()    
            
            # Get the counts and proceed
            self.counts = self.fpga.get_counts()
            # Note the total summed count
            if self.iter > 1:
                # Add them if we already started
                self.counts_total += self.counts
            else:
                # Start to accumulate the counts
                self.counts_total  = self.counts
            
            # Call a dummy function that can be overidden in an other class. 
            self.dummy_after_one_loop(self.counts, self.iter, self.rep) 

            # Note that the data are no longer reseted
            self.is_reseted = False
            
            # Allow the GUI to update. This is important to avoid freezing of the GUI inside loops
            self.process_events()    
            # Update the condition for the while loop
            condition_loop = (self.iter<self.N_loopFPGA) and self.is_running    
            _debug('GuiPulseRunner: run_loops: MIDDLE self.iter, self.N_loopFPGA, self.is_running, condition_loop',
                   self.iter,self.N_loopFPGA, self.is_running, condition_loop)
            
            # Call the function for optimizing if the condition is met
            # Note that the condition is not meet if N=0. Clever. 
            if self.Nloop_before_optimize>0:
                if self.iter%self.Nloop_before_optimize == self.Nloop_before_optimize-1:
                    _debug('GuiPulseRunner: run_loops: event_optimize sent!')
                    self.dummy_please_optimize() # Dummy function to be overid in an other class
                    # The fpga settings change during optimization. 
                    #We need to put them back.
                    self.prepare_THE_run_loop()
                            
            _debug('GuiPulseRunner: run_loops: END self.iter, self.N_loopFPGA, self.is_running, condition_loop',
                   self.iter,self.N_loopFPGA, self.is_running, condition_loop)
        
        # Loop ended.         
        # Update the buttons
        if self.is_running:
            # Click on stop if it is still running
            self.button_start_clicked()   
            
    def get_fpga_counts(self, get_total=False):
        """
        Retrieve the counts array that the FPGA output.
        
        get_total:
            (Boolean)
            If true, the method will return the accumulated counts since the begining.
            If False, the method will return the FPGA counts for the current loop. 
        """
        _debug('GuiPulseRunner: get_fpga_counts')
        if get_total:
            return self.counts_total
        else:
            return self.counts
        
        

    def dummy_after_one_loop(self, counts, iteration, rep):
        """
        DUmmy function to be overrid

        This is called after each loop (single run) of the fpga. 
        
        counts:
            Array of counts that the fpga get. 
        iteration:
            int corresponding to which iteration are we at
            
        rep:
            Number of repetition of the sequence into the fpga instruction
            """
        _debug('GuiPulseRunner: dummy_after_one_loop')

    def dummy_please_optimize(self):
        """
        Dummy method to be overid. 
        This is called each time that we want an optimization, in the method
        "run_loops". 
        For example, this dummy method should be overid by the optimization
        function of the confocal optimizer.
        """
        _debug('GuiPulseRunner: dummy_please_optimize')
        

     
    
if __name__ == '__main__':
    # Enable some debugging
    _fc._debug_enabled = False
    _debug_enabled     = True


    # Get the fpga paths and ressource number
    import spinmob as sm
    infos = sm.data.load('cpu_specifics.dat')
    bitfile_path = infos.headers['FPGA_bitfile_path']
    resource_num = infos.headers['FPGA_resource_number']
    
    
    # Get the fpga API
    fpga = _fc.FPGA_api(bitfile_path, resource_num) 
    fpga.open_session()


    self = GuiPulseRunner(fpga) 
    self.show()
    
    
     # Uncomment if we want to use the optimizer    
#    import gui_confocal_optimizer
#    optimizer = gui_confocal_optimizer.GUIOptimizer(fpga)
#    optimizer.show() # Hoh yess, we want to see it !
#    self = GuiPulseRunner(fpga,optimizer) 
#    self.show()

     # Uncomment the following for using the fake fpga api
#    fpga_fake = _fc.FPGA_fake_api(bitfile_path, resource_num) # Create the api   
#    fpga_fake.open_session()
#    self = GuiPulseRunner(fpga_fake) 
#    self.show()    
    
    # Send a simple pulse sequence for testing it
    my_seq = pulses.CoolSequence('rabi_fake').get_sequence()
    self.set_sequence(my_seq)






















