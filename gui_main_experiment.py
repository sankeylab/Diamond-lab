# -*- coding: utf-8 -*-
"""
Created on Wed Jul  1 10:39:47 2020

Main GUI for running the experiment

@author: Childresslab
"""


from spinmob import egg
import gui_confocal_main
import gui_pulser
import gui_saturation
import gui_pipulse_optimization
import gui_magnet
from converter import Converter # For converting the pattern for counting

import sys # Useful for error handling
import traceback
_p = traceback.print_last #Very usefull command to use for getting the last-not-printed error

_debug_enabled     = False

def _debug(*a):
    if _debug_enabled: 
        s = []
        for x in a: s.append(str(x))
        print(', '.join(s))
        
 

       
class GUIMainExperiment(egg.gui.Window):
    """
    Main GUI for running the experiment. 
    It contains:
        - The confocal
        - The pulser (for performing pulse sequences)
        - The frequency generator (for setting the frequency list, etc)
        
    TODO: Add the opportunity to save some combination of pulse sequence and 
          frequency generator parameters. Use tree dictionnary for that ?
    
    """
    
    def __init__(self, fpga, name="Best experiment of the world", size=[1800,1000]): 
        """
        fpga:
            "FPGA_api" object from api_fpga.py. 
            This is the object shared amoung the GUIs for controlling the fpga. 
            The session of the fpga must already be open.    
            
        size:
            size of the window. 
        """    
        _debug('GUIMainExperiment: __init__')
        _debug('Great things are done by a series of small things brought together – Vincent Van Gogh')
        
        # Run the basic stuff for the initialization
        egg.gui.Window.__init__(self, title=name, size=size)

        self.fpga = fpga
        
        # Some attribute
        self.pulse_was_running_before_optimizing = False
        self.magnet_scan_line_was_running_before_optimizing = False
        
        # Fill the GUI
        self.initialize_GUI()  
        
        # Overrid some methods
        # Overrid some methods
        self.gui_pulser.event_optimize = self.optimize_pulse        
#        self.gui_confocal.gui_optimizer.event_optimize_starts = self.before_optimization
        self.gui_confocal.gui_optimizer.event_optimize_ends   = self.after_optimization

    def initialize_GUI(self):
        """
        Fill up the GUI
        """        
        _debug('GUIMainExperiment: initialize_GUI')

        # Prepare the GUI before to place them 
        self.gui_confocal   = gui_confocal_main.GUIMainConfocal(self.fpga)
        self.gui_pulser     = gui_pulser.  GuiMainPulseSequence(self.fpga)
        self.gui_saturation = gui_saturation.     GUISaturation(self.fpga)
        self.gui_magnet     = gui_magnet.GUIMagnet()
        #Connect the magnet event methods to the proper task.
        # We do that by overridding
        self.gui_magnet.gui_sweep_lines.event_initiate_sweep = self.magnet_initiate_line_sweep
        self.gui_magnet.gui_sweep_lines.event_scan_line_checkpoint = self.magnet_scan_line_checkpoint
        # We also add an other element in the tree dictionnary, for the optimization
        self.gui_magnet.gui_sweep_lines.treeDic_settings.add_parameter('nb_line_before_optimize', 1, 
                                            type='int', 
                                            bounds=[0, None],
                                            tip='Number of line to sweep before triggering the optimization')
        self.gui_magnet.gui_sweep_lines.event_one_line_is_swept = self.magnet_scan_line_optimize
        
        
        # Replace the optimer button outside, for easy access
        self.place_object(self.gui_confocal.gui_optimizer.button_optimize,
                          row=1)   
        
        # Place a button for printing the bugs
        self.button_checkbug = egg.gui.Button('Check is everything is cool',
                                              tip='Print the last error')
        self.place_object(self.button_checkbug, row=1)
        self.connect(self.button_checkbug.signal_clicked, self.button_checkbug_clicked)
        # Plus the label for the print
        self.label_checkbug = egg.gui.Label('Welcome to the best experiment since 1992.')
        self.place_object(self.label_checkbug, row=1)
        
        # Place tabs
        self.tabs1 = self.place_object(egg.gui.TabArea(), 
                                       row=2, column=0,column_span=5, alignment=0)
        
        # Tab for the confocal
        self.tab_confocal = self.tabs1.add_tab('Confocal')
        self.tab_confocal.place_object(self.gui_confocal, alignment=0)
        
        # Tab for the pulser
        self.tab_pulser = self.tabs1.add_tab('Pulser')
        self.tab_pulser.place_object(self.gui_pulser, alignment=0)
        
        # Tab for the saturation analysis
        self.tab_saturation = self.tabs1.add_tab('Saturation curve')
        self.tab_saturation.place_object(self.gui_saturation, alignment=0)

        # Tab for the control of the magnet
        self.tab_magnet = self.tabs1.add_tab('Magnetooo')
        self.tab_magnet.place_object(self.gui_magnet, alignment=0)
        
        # Tab for miscaleneous experiment that are more complexe that simple 
        # pulse sequence
        # Each experiment will be placed into tabs2
        self.tabs2 = egg.gui.TabArea()   
        self.tab_high_level = self.tabs1.add_tab('Awesome experiment')
        self.tab_high_level.place_object(self.tabs2,
                                         row=2, column=0,column_span=5, alignment=0)
        
        # Place a tab for the pi-pulse
        self.gui_pipulse_opt = gui_pipulse_optimization.GUIPiPulseOptimization(self.gui_pulser)
        self.tab_pipulse = self.tabs2.add_tab('Pi-pulse')
        self.tab_pipulse.place_object(self.gui_pipulse_opt, alignment=0)

        # Place a tab for the adaptive Bayes
        self.tab_bayes = self.tabs2.add_tab('Adaptive Bayes')
        self.tab_bayes.place_object(egg.gui.Button('Wooho'))  
        

    def button_checkbug_clicked(self):
        """
        Print the last bug
        """     
        _debug('GUIMainExperiment: button_checkbug_clicked')  
        
        s = str(sys.last_value)
        self.label_checkbug.set_text('Last error: '+s)
        

    def optimize_pulse(self):
        """
        Optimize between loops of pulse sequences
        """
        
        # The if might be not necessary, or it is overkill.
        if not(self.gui_confocal.gui_optimizer.is_optimizing):
            
            # Only do that is it is running. 
            #TODO CLean all that. Make this more clear and clean. 
            if self.gui_pulser.is_running:
                self.pulse_was_running_before_optimizing = True
                # The if should prevent multiple click.
                i = self.gui_pulser.iter
                N_threshold = self.gui_pulser.Nloop_before_optimize
                _debug('GUIMainExperiment :optimize_pulse:  i, N = %d, %d'%(i,N_threshold))
                
                # First pause the pulse
                self.gui_pulser.button_start.click() # This should pause. 
                # Then optimize
                self.gui_confocal.gui_optimizer.button_optimize_clicked()    
                
            else:
                self.pulse_was_running_before_optimizing = False

    def after_optimization(self):
        """
        What to do after that the optimization is done.
        This will depend on what was running before the optimization. 
        """
        _debug('GUIMainExperiment: after_optimization')
        
        # The if condition might be not necessary, or it is overkill.
        if not(self.gui_confocal.gui_optimizer.is_optimizing): 
            
            if self.pulse_was_running_before_optimizing:
                # Reconvert the sequence, this is done after the pulse satrt button is clicked                
                # Re-click on for continuing the pulse sequence. 
                self.gui_pulser.button_start.click() # This continue the pulse  
                
            if self.magnet_scan_line_was_running_before_optimizing:
                # Need to reconvert the pulse sequence in the FPGA for the magnetic scan
                self.magnet_initiate_line_sweep() # Everything is done in this method
                
                
            
            # Also re-call the method of the confocal, because we just overid it :P 
            self.gui_confocal.after_optimization()

    def magnet_initiate_line_sweep(self):
        """
        Initiate the fpga for the line line of the magnet. 
        """
        _debug('GUIMainExperiment: magnet_initiate_line_sweep')
        
        # Very similiar to the method "prepare_acquisition" of GUICount
        # The main idea is to prepare the fpga for counting the right interval of time. 
        
        #First get the count time
        self.count_time_ms = self.gui_magnet.gui_sweep_lines.treeDic_settings['time_per_point']
        
        # Set the fpga NOT in each tick mode
        self.fpga.set_counting_mode(False)
        
        # Create the data array from counting
        # Prepare DIO1 in state 1
        self.fpga.prepare_DIOs([1], [1]) 
        # Get the actual DIOs, because there might be other DIOs open.
        self.dio_states = self.fpga.get_DIO_states() 
        # Convert the instruction into the data array
        conver = Converter() # Load the converter object.
        nb_ticks = self.count_time_ms*1e3/(conver.tickDuration)
        self.data_array = conver.convert_into_int32([(nb_ticks, self.dio_states)])
        
         # Send the data_array to the FPGA
        self.fpga.prepare_pulse(self.data_array)
        
    def magnet_scan_line_checkpoint(self):
        """
        Take the photocounts and update the value in the gui magnet
        """
        _debug('GUIMainExperiment: magnet_scan_line_checkpoint')
        # The fpga should already contain the pulse sequence for taking the counts
        
        # Get the counts (d'uh !)
        # Two step: runt he pulse pattern and get the counts. 
        self.fpga.run_pulse() 
        self.counts =  self.fpga.get_counts()[0]
        self.gui_magnet.gui_sweep_lines.data_w = self.counts
        
        self.counts_per_sec = 1e3*self.counts/self.count_time_ms # Just if we care   
        
    def magnet_scan_line_optimize(self):
        """
        Trigger the optimization. 
        """
        _debug('GUIMainExperiment: magnet_scan_line_optimize')
        
        # Optimizae only if the sweep is still running. 
        if self.gui_magnet.gui_sweep_lines.is_running:
            iteration = self.gui_magnet.gui_sweep_lines.iter
            m = self.gui_magnet.gui_sweep_lines.treeDic_settings['nb_line_before_optimize']
            if m != 0:
                # If it's zero, we never optimize
                if iteration % m == (m-1):
                    _debug('GUIMainExperiment: magnet_scan_line_optimize:decide to optimize')
                    
                    # Note that it was the magnet line scan that was running
                    self.magnet_scan_line_was_running_before_optimizing = True
                    # Optimize
                    self.gui_confocal.gui_optimizer.button_optimize_clicked()          
        
        

        
 
     
if __name__ == '__main__':
    
    import api_fpga 
    
    _debug_enabled     = True
    gui_pulser._debug_enabled = True
    gui_confocal_main._debug_enabled = False
    gui_pipulse_optimization._debug_enabled = False
    gui_magnet._debug_enabled = False
    import gui_confocal_optimizer
    gui_confocal_optimizer._debug_enabled = True
    api_fpga.debug_enabled = True
    
    print('Hey on es-tu bin en coton-watte')
    
     # Create the fpga api
    bitfile_path = ("X:\DiamondCloud\Magnetometry\Acquisition\FPGA\Magnetometry Control\FPGA Bitfiles"
                    "\Pulsepattern(bet_FPGATarget_FPGAFULLV2_WZPA4vla3fk.lvbitx")
    resource_num = "RIO0"     
    fpga = api_fpga.FPGA_api(bitfile_path, resource_num) # Create the api   
    fpga.open_session()
    
    self = GUIMainExperiment(fpga)
    self.show()
    
    
#    fpga_fake = _fc.FPGA_fake_api(bitfile_path, resource_num) # Create the api   
#    fpga_fake.open_session()
#    
#    self = GUIMainExperiment(fpga_fake) 
#    self.show()    
    
    
    
    
    
    
    
    
    
    
    
    
    
    