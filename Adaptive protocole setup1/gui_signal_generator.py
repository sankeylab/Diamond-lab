import numpy       as _n
import spinmob     as _s
import spinmob.egg as _egg
import mcphysics   as _mp

from api_signal_generator import signal_generator_api

_g = _egg.gui

import traceback as _traceback
_p = _traceback.print_last

# Debug stuff.
_mp.visa_tools._debug_enabled = False
_debug_enabled                = False

def _debug(*a):
    if _debug_enabled: 
        s = []
        for x in a: s.append(str(x))
        print(', '.join(s))





    

class GUISignalGenerator(_mp.visa_tools.visa_gui_base):
    """
    Graphical front-end for the Anapico signal generator.
    
    Parameters
    ----------
    name='Anapico'
        Make this unique for each object in a larger project. This 
        will also be the first part of the filename for the other settings files.
   
    show=True
        Whether to show the window immediately.
         
    block=False
        Whether to block the command line while showing the window.
    
    pyvisa_py=False
        Whether to use pyvisa_py or not.
    """

    def __init__(self, name='Anapico', show=True, block=False, timeout=2e3, write_sleep=0.02, pyvisa_py=False):
        _debug('GUISignalGenerator: __init__()')
        
        # Run the basic stuff.
        _mp.visa_tools.visa_gui_base.__init__(self, name, show, block, signal_generator_api, timeout=timeout, write_sleep=write_sleep, pyvisa_py=pyvisa_py)
    
        # Add stuff to the GUI.
        self.button_reset     = self.grid_top.add(_g.Button('Reset')).set_width(60).disable()
        self.button_rf        = self.grid_top.add(_g.Button('RF', checkable=True)).set_width(25).disable()
        self.combo_mode       = self.grid_top.add(_g.ComboBox(['Fixed', 'List'])).disable()
        self.number_dbm       = self.grid_top.add(_g.NumberBox(bounds=(-30,25),  suffix=' dBm')).disable()
        self.number_frequency = self.grid_top.add(_g.NumberBox(bounds=(1, 20e9), suffix='Hz', siPrefix=True, dec=True)).disable()
        self.number_list_index= self.grid_top.add(_g.NumberBox(0, bounds=(0,None))).disable()
        self.button_sweep     = self.grid_top.add(_g.Button('Sweep', checkable=True)).disable()
        self.number_iteration = self.grid_top.add(_g.NumberBox(0))
        
        self.grid_bot.set_column_stretch(1)
        self.tabs_data = self.grid_bot.add(_g.TabArea(self.name+'_tabs_data'), alignment=0)
        self.tab_list  = self.tabs_data.add_tab('List')
        self.button_generate_list = self.tab_list.add(_g.Button('Generate List'))
        self.button_send_list     = self.tab_list.add(_g.Button('Send List', checkable=True)).disable()
        self.label_list_status    = self.tab_list.add(_g.Label(''))
        self.tab_list.set_column_stretch(3)
        self.tab_list.new_autorow()
        self.plot_list = self.tab_list.add(_g.DataboxPlot('*.list', self.name+'_plot_list'), alignment=0, column_span=10)
        
        self.settings.add_parameter('Generate-List/f1',    1.0e9, bounds=(1.0,20e9), siPrefix=True, suffix='Hz', dec=True)
        self.settings.add_parameter('Generate-List/f2',   10.0e9, bounds=(1.0,20e9), siPrefix=True, suffix='Hz', dec=True)
        self.settings.add_parameter('Generate-List/P1',      -30, bounds=(-30,25),   suffix='dBm', type='float')
        self.settings.add_parameter('Generate-List/P2',      -30, bounds=(-30,25),   suffix='dBm', type='float')
        self.settings.add_parameter('Generate-List/Steps',   100, bounds=(2, 10000))
        self.settings.add_parameter('Generate-List/Direction', 0, values=['1->2', '2->1'])
        self.settings.add_parameter('Generate-List/Mode',      0, values=['Linear', 'Log'])
        
        self.settings.add_parameter('Sweep/Iterations', 1, bounds=(0,None), tip='How many times to sweep.')
        self.settings.add_parameter('Sweep/n1',         0, bounds=(0,None), tip='Start index.')
        self.settings.add_parameter('Sweep/n2',  10000000, bounds=(0,None), tip='Stop index (will stop at list limits).')
        
        # Connect signals
        self.button_reset        .signal_clicked.connect(self._button_reset_clicked)
        self.button_generate_list.signal_clicked.connect(self._button_generate_list_clicked)
        self.button_send_list    .signal_toggled.connect(self._button_send_list_toggled)
        self.button_sweep        .signal_toggled.connect(self._button_sweep_toggled)
        self.button_rf           .signal_toggled.connect(self._button_rf_toggled)

        self.number_dbm       .signal_changed.connect(self._number_dbm_changed)
        self.number_frequency .signal_changed.connect(self._number_frequency_changed)
        self.number_list_index.signal_changed.connect(self._number_list_index_changed)
        
        self.combo_mode.signal_changed.connect(self._combo_mode_changed)
        

        # Overloaded functions
        self.plot_list.after_load_file = self._after_plot_list_load
        

    def _after_connect(self):
        """
        Called after a successful connect.
        """
        _debug('GUISignalGenerator: _after_connect()')
        # Update the controls
        self.button_sweep.enable()
        self.button_send_list.enable()
        self.button_reset.enable()
        
        # Update the RF button.
        rf_on = self.api.get_output()
        if rf_on == None: self.button_rf.set_checked(True,  block_events=True).enable()
        else:             self.button_rf.set_checked(rf_on, block_events=True).enable()
    
        # Update the combo; we block first just in case the value doesn't "change"
        if self.api == None: self.label_instrument_name.set_text('Simulation')
        else:
            if self.api.get_mode() == 'Fixed': self.combo_mode.set_value(0, block_events=True).enable()
            else:                              self.combo_mode.set_value(1, block_events=True).enable()
            self._combo_mode_changed()
            
#            # Update the list plot if there is one
            #IT IS COMMENTED BECAUSE THERE ARE SOME BUG WHEN NO LIST IS ASSIGNED
#            self.query_list()

    def _update_gui(self):
        """
        Checks the status of the machine and updates the GUI.
        """
        
        # Update the RF button.
        rf_on = self.api.get_output()
        if rf_on == None: rf_on = True
        self.button_rf.set_checked(rf_on, block_events=True).enable()
    
        # Update the combo; we block first just in case the value doesn't "change"
        if self.api == None: self.label_instrument_name.set_text('Simulation')
        else:
            if self.api.get_mode() == 'Fixed': self.combo_mode.set_value(0, block_events=True).enable()
            else:                              self.combo_mode.set_value(1, block_events=True).enable()
            self._combo_mode_changed()
    
            #Commented for now because there are some bugs when the list doesn't exist. 
#            # Update the list plot
#            self.query_list()
                
    def _after_disconnect(self):
        """
        Called after a successful disconnect.
        """
        _debug('GUISignalGenerator: _after_disconnect()')
        self.button_sweep.disable()
        self.button_reset.disable()
        self.button_send_list.disable()
        self.button_rf.set_checked(False, block_events=True).disable()
        self.number_dbm.disable()
        self.number_frequency.disable()
        self.number_list_index.disable()
        self.combo_mode.disable()
    
    def _button_reset_clicked(self, *a):
        """
        Reset the device
        """
        self.api.reset()
        
        # Update the parameters
        self._update_gui()
    
    def _combo_mode_changed(self, *a):
        """
        Called when someone changes mode.
        """
        
        # Get the current mode.
        mode = self.api.get_mode()
        
        # Update the machine if the combo mode doesn't match
        if not mode == self.combo_mode.get_text():
            self.api.set_mode(self.combo_mode.get_text())
        
        # Get the mode again, to make sure it still matches.
        if self.api.get_mode() == 'List': 
            self.combo_mode.set_index(1, block_events=True).enable()
            self.number_list_index.set_value(self.api.get_list_index(), block_events=True).enable()
            self._number_list_index_changed()
            self.number_frequency.disable() #Disable the frequency button
            self.number_dbm.disable() #Disable the dbm button
        else:  
            #It is in fixed mode and we update the value of the button
            self.combo_mode.set_index(0, block_events=True).enable()
            self.number_frequency.set_value(self.api.get_frequency()).enable()
            self.number_dbm      .set_value(self.api.get_power()).enable()
            self.number_list_index.disable() #Change the list index. 

    def _number_dbm_changed(self, *a):
        """
        Called when someone changes the dbm.
        """
        self.api.set_power(self.number_dbm.get_value())
    
    def _number_frequency_changed(self, *a):
        """
        Called when someone changes the frequency.
        """
        self.api.set_frequency(self.number_frequency.get_value())

    def _number_list_index_changed(self, *a):
        """
        When someone changes the step number in LIST mode.
        """
        self.api.set_list_index(self.number_list_index.get_value())
        
        # Make sure.
        n = self.api.get_list_index()
        self.number_list_index.set_value(n, block_events=True)
        
        # Update the frequency and power in the safest possible way
#        fs = self.api.get_list_frequencies()
#        ps = self.api.get_list_powers()
#        self.number_dbm.set_value(ps[n])
#        self.number_frequency.set_value(fs[n])
        
        # Update the frequency and power using the graph if we have it.
        
        # If enabled, things are out of sync, get the list.
        if self.button_send_list._widget.isEnabled(): self.query_list()
        
        # Get the power and frequency from the plot
        self.number_dbm      .set_value(self.plot_list['P_dBm'][n])
        self.number_frequency.set_value(self.plot_list['f_Hz'][n])
        
            
            
    def query_list(self):
        """
        Asks the instrument for the list values and updates the plot_list.
        """
        self.plot_list.clear()
        self.settings.send_to_databox_header(self.plot_list)
        
        self.label_list_status.set_text('Getting frequencies and powers.')
        self.window.process_events()
        
        fs = self.api.get_list_frequencies()
        ps = self.api.get_list_powers()
        if fs == None or ps == None: return
        
        if not len(fs) == len(ps):
            print("ERROR query_list(): List lengths do not match. len(fs)="+str(len(fs))+' len(ps)='+str(len(ps)) )
        
        N  = len(fs)
        self.plot_list['n'] = _n.linspace(0, N-1, N)
        self.plot_list['f_Hz']  = fs
        self.plot_list['P_dBm'] = ps
        
        self.label_list_status.set_text(str(N) + ' points in list memory')
        self.plot_list.plot()
        self.button_send_list.disable()
        self.window.process_events()
            
    def _button_generate_list_clicked(self, *a):
        """
        Creates a ramp the frequency and power list.
        """
        _debug('GUISignalGenerator: _button_generate_list_clicked()', a)
        
        N = self.settings['Generate-List/Steps']
        
        # Generate a list in the direction we wish to step
        if self.settings['Generate-List/Direction'] == '1->2':
            f1 = self.settings['Generate-List/f1']
            f2 = self.settings['Generate-List/f2']
            d1 = self.settings['Generate-List/P1']
            d2 = self.settings['Generate-List/P2']
        else:
            f1 = self.settings['Generate-List/f2']
            f2 = self.settings['Generate-List/f1']
            d1 = self.settings['Generate-List/P2']
            d2 = self.settings['Generate-List/P1']
        
        # Get the powers in mW
        P1 = 10**(d1/10.0)
        P2 = 10**(d2/10.0)
        
        # Clear the plot
        self.plot_list.clear()
        self.settings.send_to_databox_header(self.plot_list)

        # Indices
        self.plot_list['n'] = _n.linspace(0, N-1, N)
        
        # Create the sweep in either linear or log space.
        if self.settings['Generate-List/Mode'] == 'Linear':
            self.plot_list['f_Hz']  = _n.linspace(f1, f2, N)
            self.plot_list['P_dBm'] = 10*_n.log10(_n.linspace(P1, P2, N))
        
        # Log steps
        else:
            self.plot_list['f_Hz']  = _s.fun.erange(f1, f2, N)
            self.plot_list['P_dBm'] = _n.linspace  (d1, d2, N)
        
        # Plot it
        self.plot_list.plot()
        self.window.process_events()
        
        # Enable send list
        self.button_send_list.enable()
        
        # Remove visible knowledge
        self.label_list_status.set_text('Shown list does not match device list.')
    
    def _after_plot_list_load(self):
        """
        Called when someone loads a plot_list.
        """
        self.button_send_list.enable()
        self.label_list_status.set_text('Shown list does not match device list.')
        
    def _button_send_list_toggled(self, *a):
        """
        Send the list to the anapico.
        """
        _debug('GUISignalGenerator: _button_send_list_toggled()', a)
        
        if not self.button_send_list.is_checked(): return
        
        # Clear the label
        self.label_list_status.set_text('')
        self.window.process_events()

        # If there is data to send
        if len(self.plot_list): 
            
            # Reset
#            self.label_list_status.set_text('Resetting...')
#            self.window.process_events()
#            self.api.reset()
        
            # Send it
            self.label_list_status.set_text('Sending...')
            self.window.process_events()
            self.api.send_list(self.plot_list['f_Hz'], self.plot_list['P_dBm'], 
                               dwell=1000, delay=0)
            
        # Check it
        self.label_list_status.set_text('Double-checking...')
        self.window.process_events()
        self.query_list()
    
        # Update the RF button
        self.button_rf.set_checked(self.api.get_output(), block_events=True)
        
        # Undo the button
        self.button_send_list.set_checked(False, block_events=True)
                        
    
    def _button_sweep_toggled(self, *a):
        """
        Dummy function to overload. Just waits 0.25 seconds on each step.
        """
        _debug('GUISignalGenerator: _button_sweep_toggled()', a)
        
        # Only run the sweep if we have enabled the button
        if self.button_sweep.is_checked():
            
            # Run the "before sweep" setup function for the user to overwrite 
            # (default is just a pause)
            self.before_sweep()
            
            # Set list mode
            self.combo_mode.set_index(1)
            self.api.set_mode('List') #Set the mode to list !!
            # Update the RF button
            self.button_rf.set_checked(self.api.get_output(), block_events=True)
            
            
            # Get list length from the generator
            ps = self.api.get_list_powers()
            fs = self.api.get_list_frequencies()
            
            # Make sure they match!
            if not len(ps) == len(fs): 
                print("ERROR: Lengths of power and frequency lists do not match!")
                return
            
            
            # Update the user
            self.label_list_status.set_text(str(len(fs)) + ' points in list memory')
            
            # Loop for the number of iterations
            self.number_iteration.set_value(0)
            while self.number_iteration.get_value() < self.settings['Sweep/Iterations'] \
               or self.settings['Sweep/Iterations'] <= 0:
            
                # Break out if canceled
                if not self.button_sweep.is_checked(): break
                
                # Loop
                for n in range(self.settings['Sweep/n1'], min(self.settings['Sweep/n2'], len(fs))):
                    
                    # Break out if canceled
                    if not self.button_sweep.is_checked(): break
                
                    # Set the list index, which updates the machine
                    self.api.set_list_index(n)
                    #I'm adding these lines to debug the fact that Api doesn't change the frequency of its output. 
                    _debug(self.api.get_list_index(), self.api.get_frequency(), self.api.get_power())
                    #print(self.api.get_list_frequencies())
                    
                    self.number_list_index.set_value(n,     block_events=True)
                    self.number_frequency .set_value(fs[n], block_events=True)
                    self.number_dbm       .set_value(ps[n], block_events=True)
                    self.window.process_events()
                    
                    # This is where you could insert some interesting code.
                    self.after_sweep_set_list_index()
            
                # Increase the iteration count
                self.number_iteration.increment()
                
                # Run user code
                self.after_single_sweep()
            
            # Run user code
            self.after_all_sweeps()
            
            # All done with the loop. Disable the sweep button!
            # We put this after the user functions so they can tell if
            # someone manually quit out of the loop.
            self.button_sweep.set_checked(False, block_events=True)
    
    def before_sweep(self):
        """
        Dummy function to overload with functionality to perform before the 
        sweep begins.
        """
        _debug('GUISignalGenerator: before_sweep()')
        self.window.sleep(0.05)
    
    def after_sweep_set_list_index(self):
        """
        Dummy function (just a 0.05 second pause) to overwrite for doing 
        stuff just after setting the list index in the list sweep.
        """
        _debug('GUISignalGenerator: after_sweep_set_list_index()')
        self.window.sleep(0.05)
    
    def after_single_sweep(self):
        """
        Dummy function to overwrite for doing something after the
        list sweep is complete.
        """
        _debug('GUISignalGenerator: .after_single_sweep()')
        self.window.sleep(0.05)
    
    def after_all_sweeps(self):
        """
        Dummy function to overwrite for doing something after all 
        the sweeps are done (iteration = iterations)
        """
        _debug('GUISignalGenerator: after_all_sweeps()')
        self.window.sleep(0.05)
        
    def _button_rf_toggled(self, *a):
        """
        Turns the output on or off.
        """
        _debug('GUISignalGenerator: _button_rf_toggled()', a)
        # Set
        self.api.set_output(self.button_rf.is_checked())
        
        # Verify
        self.button_rf.set_checked(self.api.get_output(), block_events=True)
        
        # Make the background colored, because other on remote desktop it is very not clear
        if self.button_rf.is_checked():
            self.button_rf.set_style('background-color: rgb(20, 200, 20);')
        else:
            self.button_rf.set_style('background-color: rgb(200, 0, 200);')  
            
#        #The mode of the SMA switch to Fixed when the RF are off
#        self._combo_mode_changed()
        


        
        
        
     

        
if __name__ == '__main__':
    
    _mp.visa_tools._debug_enabled = True
    _debug_enabled                = True
    
    #self = GUISignalGenerator()
    #self = signal_generator_api('SMA100B') #This will not pop-out the GUI
    self = GUISignalGenerator('Anana') #This will pop-out the GUI
    
    # Note the api for quickly make tests
    # For sending query, type a.query(YOUR_QUERY)
    # For writting thing, type a.write(YOUR_QUERY)
    a = self.api 
   
   
   
   
   