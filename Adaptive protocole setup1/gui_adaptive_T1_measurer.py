# -*- coding: utf-8 -*-
"""
Created on Thu Oct  8 11:39:41 2020

Goal: define the measurer for the adaptive protocole of T1

@author: Childresslab
"""


# The following is for building the pulse
from pulses import ChannelPulses, PulsePatternBlock, Sequence
import api_fpga as _fc

import gui_pulse_runner
import gui_signal_generator

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







        

class GUIProbe2StatesOneTime(egg.gui.Window):
    """
    GUI for making the following measurement:
        Preparing the states and let them decay until a single probed time.
    
    If probe 2 |ms> states at the same decay time. 
    
    """   
    
    def __init__(self, fpga, name="Single probe T1 2 states", size=[1000,500]): 
        """
        Initialize

        fpga:
            "FPGA_api" object from api_fpga.py. 
            This is the object shared amoung the GUIs for controlling the fpga. 
            The session of he fpga must already be open.      
        
        
        """    
        _debug('GUIProbe2StatesOneTime:__init__')
        _debug('If you’re the smartest person in the room, you’re in the wrong room. – Unknown')
        
        # Run the basic stuff for the initialization
        egg.gui.Window.__init__(self, title=name, size=size)

        # Steal the fpga, mouhahaha
        self.fpga = fpga
        # Overid a method that, hopefully, should prevent the freeze out of the
        # gui for long pulse sequence.
        self.fpga.dummy_event_pulse_is_long = self.process_events
        
        # Initialise the GUI
        self.initialize_GUI()
        
    def initialize_GUI(self):
        """
        Fill up the GUI
        """        
        _debug('GUIProbe2StatesOneTime: initialize_GUI')
        _debug('Punctuality is not just limited to arriving at a place at right time, it is also about taking actions at right time. ― Amit Kalantri')
        
        # A button for preparing stuff
        self.button_prepare_experiment = egg.gui.Button('Prepare all settings',
                                                        tip='Prepare the measurement before running')
        self.place_object(self.button_prepare_experiment, row=0, column=0)
        self.connect(self.button_prepare_experiment.signal_clicked, 
                     self.button_prepare_experiment_clicked)
        
        # Add the pulse runner
        self.gui_pulse_runner = gui_pulse_runner.GuiPulseRunner(self.fpga)
        self.place_object(self.gui_pulse_runner, 
                          row=1, column=0, column_span=2)
        
        # Add the signal generator
        self.sig_gen = gui_signal_generator.GUISignalGenerator(show=False)
        self.gui_sig_gen    = self.sig_gen.window    
        self.place_object(self.gui_sig_gen, 
                          row=1, column = 2)
        
        # tree dictionnarry for the settings
        self.treeDic_settings = egg.gui.TreeDictionary(autosettings_path='setting_T1_singleTime_2states')
        self.place_object(self.treeDic_settings, row=2, column=0, column_span=2)

        self.treeDic_settings.add_parameter('Power', -20, 
                                            type='float', step=1, decimals=10,
                                            bounds=[-50,30], suffix=' dBm',
                                            tip='Constant power of the RF for the pipulse')
        self.treeDic_settings.add_parameter('Frequency', 3, 
                                            type='float', step=0.1, decimals=10,
                                            bounds=[0,10], suffix=' GHz',
                                            tip='Frequency of the RF for the pipulse') 
        
        self.treeDic_settings.add_parameter('t_probe', 10, 
                                            type='float', step=0.1, decimals=10,
                                            bounds=[0,None], suffix=' us',
                                            tip='Time to probe.') 

        self.treeDic_settings.add_parameter('dt_pi_pulse', 0.3, 
                                            type='float', step=0.1, decimals=10,
                                            bounds=[0,None], suffix=' us',
                                            tip='Duration of pi pulse') 
        
        self.treeDic_settings.add_parameter('dt_laser_initiate', 3, 
                                            type='float', step=0.1, decimals=10,
                                            bounds=[0,None], suffix=' us',
                                            tip='Duration of laser for initiating into ms=0')  
        self.treeDic_settings.add_parameter('dt_wait_after_initiate', 1.1, 
                                            type='float', step=0.1, decimals=10,
                                            bounds=[0,None], suffix=' us',
                                            tip='Duration of time to wait between the laser initialization into ms=0 and the pi-pulse') 
        
        self.treeDic_settings.add_parameter('dt_readout', 0.4, 
                                            type='float', step=0.1, decimals=10,
                                            bounds=[0,None], suffix=' us',
                                            tip='Duration of the readout') 
        self.treeDic_settings.add_parameter('delay_read_before_laser', 0.05, 
                                            type='float', step=0.01, decimals=10,
                                            bounds=[0,None], suffix=' us',
                                            tip='Delay that we read before shining the laser')  
        
        self.treeDic_settings.add_parameter('DIO_laser', 2, 
                                            type='int', step=1, 
                                            bounds=[0,16],
                                            tip='DIO for the laser')          
        self.treeDic_settings.add_parameter('DIO_pulse_modulation', 3, 
                                            type='int', step=1, 
                                            bounds=[0,16],
                                            tip='DIO for modulating the pi pulse. AKA for sending the RF.')  

        self.treeDic_settings.add_parameter('DIO_sync_scope', 5, 
                                            type='int', step=1, 
                                            bounds=[-1,16],
                                            tip='DIO for synchronizing the oscilloscope. Put -1 for nothing')

        # Add a Data Box plotter for the incoming data
        self.databoxplot = egg.gui.DataboxPlot(autosettings_path='plot_probeOneTime_2states')
        self.place_object(self.databoxplot, 
                          row=2, column = 1, row_span=2, column_span=2) 
        self.databoxplot.button_multi.set_value(False) # Make all on the same plot
        
        # Make a label for showing some estimate
        self.label_estimates = egg.gui.Label('We have the best T1 prober on the market.')
        self.place_object(self.label_estimates, row=2, column=3, alignment=1)        

    def button_prepare_experiment_clicked(self):
        """
        Prepare the experiment:
            Prepare the pulse sequence in the fpga
            Prepare the signal generator
            Prepare the plot
        """
        _debug('GUIProbe2StatesOneTime: button_prepare_experiment_clicked')   

        # Prepare the sequence accoring to the best knowledge that we have so far. 
        self.prepare_pulse_sequence()
        
        # We want the fpga NOT in each tick mode
        self.gui_pulse_runner.CheckBox_CET_mode.set_checked(value=False)
        
        # The following lines is for giving the sequence with delays
        # Remove the delay if there was previously
        if self.gui_pulse_runner.sequence_has_delay:
            self.gui_pulse_runner.button_set_delays.click()
        # Set the sequence
        self.gui_pulse_runner.set_sequence( self.sequence )
        # Set the delay
        self.gui_pulse_runner.button_set_delays.click()
        
        # Get the setting for the signal generator
        self.P    = self.treeDic_settings['Power']
        self.f    = self.treeDic_settings['Frequency']
        
        # Prepare the signal generator for the specific sequence
        # The first signal generator
        #THE ORDER OF WHICH METHOD TO CALL FIRST MIGHT MATTER
        self.sig_gen.button_reset.click()  # Reset the parameters 
        self.sig_gen.api.prepare_for_Rabi() # Prepare the internal parameters of the machine
        self.sig_gen.combo_mode.set_value(index=0) # Set in Fixed mode
        self.sig_gen.number_dbm      .set_value(self.P)
        self.sig_gen.number_frequency.set_value(self.f*1e9 )#Convert into Hz
        # Turn on the RF !
        if not(self.sig_gen.button_rf.is_checked()):
            self.sig_gen.button_rf.set_checked(True)
            
        
        # Overid the method for dealing after the loop.
        self.gui_pulse_runner.dummy_after_one_loop = self.after_one_loop        
       
        
    def prepare_pulse_sequence(self):
        """
        Prepare the pulse sequence. 
        It generates the objet to be converted into a data array. 
        """
        _debug('GUIProbe2StatesOneTime: prepare_pulse_sequence')
        
        DIO_laser         = self.treeDic_settings['DIO_laser']
        DIO_PM          = self.treeDic_settings['DIO_pulse_modulation']
        DIO_sync          = self.treeDic_settings['DIO_sync_scope']
        
        dt_laser      = self.treeDic_settings['dt_laser_initiate'] # Interval of time for shining the laser
        dt_readout    = self.treeDic_settings['dt_readout']
        dt_wait_ms0_pi= self.treeDic_settings['dt_wait_after_initiate'] #How much time to wait between ms=0 and pi pulse
        dt_pi_pulse   = self.treeDic_settings['dt_pi_pulse'] # Duration of the pi-pulse
        delay_read    = self.treeDic_settings['delay_read_before_laser'] # Delay (us) that we read before shining the laser 
            
        self.t_probe = self.treeDic_settings['t_probe']
        
        dt_sync_scope = 1   # Duration of the trigger for synchronizing the scope (us)
        
        # WE NOW BUILT THE SEQUENCE
        # To be efficient, we gonna use the laser for reading and as an 
        # initialization in ms=0 for the next measurement. 

        # Initiate the sequence on which we gonna construct
        sequence = Sequence(name='T1 2 states at single probing time')

        # Create a channel for the synchronization with the scope. 
        channel_sync = ChannelPulses(channel=DIO_sync, name='Sync oscilloscope')
        channel_sync.add_pulses([0, dt_sync_scope]) 
        
        # We gonna do three steps: iniate and read ms0, 1 and -1
        
        # Laser channel for each ms state
        channel_laser = ChannelPulses(channel=DIO_laser, name='Laser')      
        # Read channel for each state
        channel_read  = ChannelPulses(channel=1, name='Read')
        # Channel for the Pi-pulse initializing
        channel_RF    = ChannelPulses(channel=DIO_PM , name='Pi pulse')     
        
        # Set the reference time
        t0 = dt_sync_scope

        # First prepare the state  ms=0 
        channel_laser.add_pulses([t0, t0+dt_laser])
        
        # Let evolve the state
        tref = channel_laser.get_pulses_times()[-1] + self.t_probe
        
        # Read it. Start to read slightly a little bit before the laser is shone
        channel_read.add_pulses([tref - delay_read, tref + dt_readout])    
        
        # Shine the laser for both reading and for initializing into ms=0
        channel_laser.add_pulses([tref, tref+dt_laser])

        # Update the reference time
        t0 = channel_laser.get_pulses_times()[-1]
            
        # At this point, the state is ms=0
        
        # Let's flip the state into ms=-1 or ms=+1 (depending on the type of the frequency of the pulse)
        # Note at which time to start the RF for flipping the state
        tref_RF = t0 + dt_wait_ms0_pi
        # Send the pi-pulse
        channel_RF.add_pulses([tref_RF, tref_RF + dt_pi_pulse]) # Flip in ms=-1
        
        # Let evolve the state 
        tref = channel_RF.get_pulses_times()[-1] + self.t_probe 
        # Read it. Start to read slightly a little bit before the laser is shone
        channel_read.add_pulses([tref - delay_read, tref + dt_readout])  

        # Shine the laser for both reading and for initializing into ms=0
        channel_laser.add_pulses([tref, tref+dt_laser])          

        # Update the reference time
        t0 = channel_laser.get_pulses_times()[-1]
                
        # At this point, the state is ms=0       
            
        # Read again at the end for the reference
        t0 = channel_laser.get_pulses_times()[-1]
        channel_read.add_pulses([t0 - dt_readout, t0])  


                
                
                
        # Add all that masterpiece to a block
        block = PulsePatternBlock(name='Block tprobe = %.2f us'%self.t_probe)
        block.add_channelEvents([channel_laser, 
                                 channel_RF, 
                                 channel_read])
        # Add the trigger for synchronizing the scope only on the first block
        block.add_channelEvents([channel_sync])
        
        # Add the block to the sequence
        sequence.add_block(block)             
            
        self.sequence =  sequence

    def databoxplot_update(self):
        """
        Update the plot
        """
        _debug('GUIProbe2StatesOneTime: databoxplot_update')
        
        # Clear the plot
        self.databoxplot.clear() 
        
        # Feed the databox plot with the data
        self.databoxplot['ms0']   = self.count_per_iter_ms0_s
        self.databoxplot['ms-+1'] = self.count_per_iter_msmp1_s
        self.databoxplot['ref']   = self.count_per_iter_ref_s
        
        # Add important information in the header
        self.databoxplot.insert_header('repetition', self.rep)
        self.databoxplot.insert_header('iteration' , self.iteration)
        for key in self.treeDic_settings.get_keys():
            # Add each element of the dictionnary three
            self.databoxplot.insert_header(key , self.treeDic_settings[key])
        
        # Show it
        self.databoxplot.plot()   
        
    def after_one_loop(self, counts, iteration, rep):
        """
        What to do after one loop of the fpga. 

        This is called after each loop (single run) of the fpga. 
        
        counts:
            Array of counts that the fpga get. 
        iteration:
            int corresponding to which iteration are we at
            
        rep:
            Number of repetition of the sequence into the fpga instruction
            """
        _debug('GUIT1probeOneTimes: after_one_loop')
        
        # Note that for saving 
        self.rep = rep
        self.iteration = iteration
        self.counts_prior_to_process = counts # Save it for debugging
        
        # Get the counts per readout per block
        self.count_processor = _fc.ProcessFPGACounts(counts)
        
        # We only have one block we 4 readout in it. 
        
        # Get the array of counts 
        self.counts_per_block_s =  self.count_processor.get_sum_count_per_block(rep, 1)
        
        # Get the number of counts for each measurement
        self.counts_ms0   = self.counts_per_block_s[0][0] 
        self.counts_msmp1 = self.counts_per_block_s[0][1]
        self.counts_ref   = self.counts_per_block_s[0][2]
        
        # If its the first iteration
        if iteration == 0:
            # Note the total number of readout for each state
            self.total_nb_readout = rep
            # Get the summed count per iteration
            self.count_per_iter_ms0_s   = [self.counts_ms0 ]
            self.count_per_iter_msmp1_s = [self.counts_msmp1]
            self.count_per_iter_ref_s   = [self.counts_ref ]
        else:
            # Note the total number of readout for each state
            self.total_nb_readout += rep
            # Appened the summed count per iteration
            self.count_per_iter_ms0_s  .append( self.counts_ms0)
            self.count_per_iter_msmp1_s.append( self.counts_msmp1)
            self.count_per_iter_ref_s  .append( self.counts_ref)
        
        # Update the plot
        self.databoxplot_update()
            
        # Update the label
        self.mean_count_per_readout_ms0   = np.sum(self.count_per_iter_ms0_s  )/rep/iteration
        self.mean_count_per_readout_msmp1 = np.sum(self.count_per_iter_msmp1_s)/rep/iteration
        self.mean_count_per_readout_ref   = np.sum(self.count_per_iter_ref_s  )/rep/iteration
        
        text = (  'Mean count per readout'+
                '\nms0   : %f'%self.mean_count_per_readout_ms0 +
                '\nms-+1 : %f'%self.mean_count_per_readout_msmp1 +
                '\nref   : %f'%self.mean_count_per_readout_ref)
        self.label_estimates.set_text(text)        

        
     
        
if __name__=="__main__":
    _debug_enabled = True
    
    # Get the fpga paths and ressource number
    import spinmob as sm
    infos = sm.data.load('cpu_specifics.dat')
    bitfile_path = infos.headers['FPGA_bitfile_path']
    resource_num = infos.headers['FPGA_resource_number']
    # Get the fpga API
    fpga = _fc.FPGA_api(bitfile_path, resource_num) 
    fpga.open_session()
    
    
    
#    import api_fpga as _fc
#    fpga_fake = _fc.FPGA_fake_api(bitfile_path, resource_num) # Create the api   
#    fpga_fake.open_session()
#
#    import gui_pulser
#    gui = gui_pulser.GuiMainPulseSequence(fpga_fake)
#    gui.show()


       
#    self = GUIProbe3StatesOneTime(pulser, size=[1500,800])
#    self.show()
    
    self = GUIProbe2StatesOneTime(fpga, size=[1800,800])
    self.show()            
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
