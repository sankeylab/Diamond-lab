# -*- coding: utf-8 -*-
"""
Created on Wed Apr 15 16:20:21 2020

Goal: Define the classes for defining general pulse sequences. 

TODO Explain the structure
singleChannel pulses → (pulsePattern forms a block) → sequence of blocks. 



@author: Michael
"""


import numpy as np
import matplotlib.pyplot as plt

import traceback
_p = traceback.print_last #Very usefull command to use for getting the last-not-printed error


# Debug stuff.
_debug_enabled                = False

def _debug(*a):
    if _debug_enabled: 
        s = []
        for x in a: s.append(str(x))
        print(', '.join(s))


class ChannelPulses():
    """
    Class for defining a list of event of one DIO channel. 
    This can be more than one pulse.
    Note that there is no necessity to define all the events for one channel
    with a single object. Especially if one channel have different purpose, 
    at different time. 
    
    The relevant attributes of this class are:
    channel: the channel at which the events are occcuring
    name: The name or tag for this combination of channel and list of event. 
    times_tick: array of ticks at which the raises and the falls occur. 
    
    """
    
    def __init__(self, channel=0, name='action', tickDuration=1/120 ): 
        """
        Input
        channel: which channel does the events occurs.
        name: name to give to this channel. 
        tickDuration: Duration of a ticks in us. This defines the granulation 
                      of time.   
        
        """    
        self.tickDuration = tickDuration 
        self.channel = channel
        self.name = name
        
        # This will contain the times (in ticks) at which the channel is turned ON and OFF
        self.times_tick = np.array([]) # 
         
        
    def timeIntoTicks(self, t):
        """
        Convert the time (in us) into number ticks. 
        Input
        t: time (in us) to be converted into tick.  
        """
        return  np.round(t/self.tickDuration)    
    
    def set_name(self, name):
        """
        Set the name of the channel
        """
        self.name = name
        
    def get_name(self):
        """
        Get the name of the channel
        """
        return self.name       
    
    def set_channel(self, channel):
        """
        Set the channel to channel. 
        """
        self.channel = channel
    
    def get_channel(self):
        """
        Return the channel
        """
        return self.channel
    
    def get_pulses_tick(self):
        """
        Return the times (in ticks) of the raise/fall of the pulses
        """
        return self.times_tick
    
    def get_pulses_times(self):
        """
        Return the time (in us) of the raise/fall of the pulses
        """
        return self.times_tick*self.tickDuration
    
    
    def add_pulses(self, times):
        """
        Add a list of times at which the channelon is turn ON and OFF. 
        This list of time is converted into ticks
        
        Input
        times: array of times (us) at which the channel is turn ON and OFF.
               Must have an even number of element !
                “even-indexed” elements correspond to the raise and the
                “odd-indexed” elements correspond to the fall.
        """
        # Make sure that the number of event is even.
        if len(times)%2 !=0:
            print('Error ! Must have an even number of times !')
            return
        # Convert in numpy array 
        if type(times) != np.ndarray:
            times = np.array(times)
        # Convert the time into ticks    
        ts_tick = self.timeIntoTicks(times)
        # Add these times to the total times
        self.times_tick = np.concatenate((self.times_tick, ts_tick))
        
    def add_trainPulses(self, t0, tOn, tOff, nbWagon):
        """
        Input:
        DIO:    DIO channel at which to apply the pulse train
        t0:   Time at which to start the train of pulse (starting as a raise) (us)
        tOn:  Time interval for the ON state of the train (us). 
        tOff: Time interval for the OFF state of the train (us)
        nbWagon: Number of pulses that the train contain. 
        """
#        # Convert time into ticks
#        t0   = self.timeIntoTicks(t0)
#        tOn  = self.timeIntoTicks(tOn)
#        tOff = self.timeIntoTicks(tOff)
#        
        # Create the train of pulses
        ts = [t0]
        for i in range(nbWagon-1):
            # Add a wagon
            ts.append( ts[-1] + tOn )
            ts.append( ts[-1] + tOff)
        # Add the last time to fall
        ts.append(ts[-1] + tOn)
        # Add these times to the total times
        self.add_pulses(ts)
    
class PulsePatternBlock():
    """
    Class for a pulse pattern. 
    TODO explain clearly the structure
    
    The relevant attributes of this class are:
    pulse_pattern: list of "channel-events", where "channel-events" defines a set 
                   of event for a given channel.
    name: a name or tag for this combination of pulse instructions (example: Rabi, T1) 
       
    """
    def __init__(self, name='Neat pulse pattern', tickDuration=1/120): 
        """
        Input
        
        tickDuration: Duration of a ticks in us. This defines the granulation 
                      of time.   
        
        """    
        self.tickDuration = tickDuration 
        self.name = name
        
        # Each element will be a set of event for a given channel
        self.pulse_pattern = [] 

    def set_name(self, name):
        """
        Set the name of the object
        """
        self.name = name
        
    def get_name(self):
        """
        Get the name of the object
        """
        return self.name               
    
    def get_pulse_pattern(self):
        """
        Return the pulse_pattern
        """
        return self.pulse_pattern
    
    def get_nb_channel_events(self):
        """
        Returnt the number of channel event. 
        """
        return len(self.pulse_pattern)
    
    def add_channelEvents(self, channel_events):
        """
        Add a ChannelPulses object to the PulsePatternBlock
        
        Input:
            channel_events
            ChannelPulses object or list of ChannelPulses object to be added. 
        """
        if type(channel_events) == list:
            for c_e in channel_events:
                self.pulse_pattern.append(c_e)
        else:
            self.pulse_pattern.append(channel_events)
        
class Sequence():
    """
    Class for defining a sequence of blocks. 
    Each block is a pulse pattern with various parameters
    Each block is a PulsePatternBlock
    
    """
    def __init__(self, name='BonjourHi'): 
        """
        name: name to give to this sequence
        """
        self.name = name 
        
        self.block_s = [] # List of PulsePatternBlock
        
        self.nb_block = 0 #Number of block within the sequence 
        
    def set_name(self, name):
        """
        Set the name of the object
        """
        self.name = name
        
    def get_name(self):
        """
        Get the name of the object
        """
        return self.name
    
    def get_nb_block(self):
        """
        Get hte number of block within the sequence
        """
        return self.nb_block
             
    def get_block_s(self):
        """
        Return the PulsePatternBlock in the sequence
        """
        return self.block_s
    
    def add_block(self, pulse_block):
        """
        Add a single block of pulse sequence to the sequence
        
        Input
        pulse_pattern: pulsePatternBlock object to add to the sequence
        """
        self.block_s.append(pulse_block)
        self.nb_block += 1 # Update it instead of taking the lenght of sequence to speed up
        

def add_raise_delays(sequence, DIOs, delays):
    """
    Add raise delays into each channel of the sequence.
    
    sequence:
        Object Sequence on which we want to add the deldays. 
    DIOs: 
        list of DIOs for which we want to add the delays. 
    delays:
        list of delays (us) associated with the list of DIOs. 
        Obviously, the lenght of delays must match the lenght of DIOs ;)
    """
    
    if not(len(DIOs) == len(delays)):
        print('ERROR: in add_raise_delays, the lenght of DIOs do not match the lenght of delays ! Have a good day.')
        return
    
    # Transform into numpy array for the subsequent manipulation
    DIOs   = np.asarray(DIOs)
    delays = np.asarray(delays)
    
    # Initiate the sequence with delays, with a slighly modified name
    new_sequence = Sequence(sequence.get_name()+'_with_delay')
    
    # Scan each block
    for i, block in enumerate(sequence.get_block_s()):
        # Initiate the new block with a slighly modified name
        new_block = PulsePatternBlock(block.get_name()+'_with_delay')
        
        # For each block, go trough each channel to add the delay
        for j, pulse in enumerate(block.get_pulse_pattern()):
            
            # Get the channel
            channel = pulse.get_channel()
            if channel in DIOs:
                # If the channel correspond to one for which we want to add a delay
                condition = channel == DIOs # An array of boolean, true where the condition is met. 
                delay = delays[condition] # That catches the corresponding delay
                _debug('Channel %d has a raise delay of %f us'%(channel, delay))
            
                # Initiate the new channel with a slighly modified name
                new_name = pulse.get_name()+'_with_delay'
                new_pulse = ChannelPulses(channel=channel, name=new_name)
                
                # Add the delay !! (Finnanly lol)
                # Get the times
                old_times = pulse.get_pulses_times()
                new_times = np.zeros(len(old_times))
                # Now add the delay on the raises !
                # The even element correspond to raise time for which we add the delays
                for k, time in enumerate(old_times):
                    if k%2==0:
                        new_times[k] = time + delay
                    else:
                        new_times[k] = time
                        
                # Update the new pulse with thuis delay
                new_pulse.add_pulses(new_times)
                
            else:
                # If there is no delay to add, de new pulse is just the input pulse 
                new_pulse = pulse
                
            # Add the new pulse to the new block
            new_block.add_channelEvents(new_pulse)
        # Add the new block to the new sequence
        new_sequence.add_block(new_block)
        
    # Return the new sequence ;)
    return new_sequence

def add_fall_delays(sequence, DIOs, delays):
    """
    Add fall delays into each channel of the sequence.
    
    sequence:
        Object Sequence on which we want to add the delays. 
    DIOs: 
        list of DIOs for which we want to add the delays. 
    delays:
        list of delays (us) associated with the list of DIOs. 
        Obviously, the lenght of delays must match the lenght of DIOs ;)
    """
    
    if not(len(DIOs) == len(delays)):
        print('ERROR: in add_fall_delays, the lenght of DIOs do not match the lenght of delays ! Have a good day.')
        return
    
    # Transform into numpy array for the subsequent manipulation
    DIOs   = np.asarray(DIOs)
    delays = np.asarray(delays)
    
    # Initiate the sequence with delays, with a slighly modified name
    new_sequence = Sequence(sequence.get_name()+'_with_delay')
    
    # Scan each block
    for i, block in enumerate(sequence.get_block_s()):
        # Initiate the new block with a slighly modified name
        new_block = PulsePatternBlock(block.get_name()+'_with_delay')
        
        # For each block, go trough each channel to add the delay
        for j, pulse in enumerate(block.get_pulse_pattern()):
            
            # Get the channel
            channel = pulse.get_channel()
            if channel in DIOs:
                # If the channel correspond to one for which we want to add a delay
                condition = channel == DIOs # An array of boolean, true where the condition is met. 
                delay = delays[condition] # That catches the corresponding delay
                _debug('Channel %d has a fall delay of %f us'%(channel, delay))
            
                # Initiate the new channel with a slighly modified name
                new_name = pulse.get_name()+'_with_delay'
                new_pulse = ChannelPulses(channel=channel, name=new_name)
                
                # Add the delay !! (Finnanly lol)
                # Get the times
                old_times = pulse.get_pulses_times()
                new_times = np.zeros(len(old_times))
                # Now add the delay on the falls !
                # The odd elements correspond to fall time for which we add the delays
                for k, time in enumerate(old_times):
                    if k%2==1:
                        new_times[k] = time + delay
                    else:
                        new_times[k] = time
                        
                # Update the new pulse with this delay
                new_pulse.add_pulses(new_times)
                
            else:
                # If there is no delay to add, de new pulse is just the input pulse 
                new_pulse = pulse
                
            # Add the new pulse to the new block
            new_block.add_channelEvents(new_pulse)
        # Add the new block to the new sequence
        new_sequence.add_block(new_block)
        
    # Return the new sequence ;)
    return new_sequence        
    
    
    
    
    
    
    
      
# =============================================================================
# Plotting function for the pulse pattern.
# =============================================================================       
class GUIPulsePattern():
    """
    GUI to show the initial pulse pattern. 
    The GUI permits to double click to show the times 
    """
    def __init__(self, pulse_sequence): 
        """
        Initialize by sending the pulse pattern to plot.
        
        pulse_sequence:
            Sequence object,containing all the block to plot
        """    
        self.pulse_sequence = pulse_sequence
        self.nb_block = pulse_sequence.get_nb_block() # Total number of block in the sequence
        self.block_s = self.pulse_sequence.get_block_s()
        self.ind_block = 0 # Index of the block to see
        #Some usefull variables
        self.nbLines = 0 #Number of lines for the times
        
        # Initialize the figure and axis
        self.fig, self.ax = plt.subplots(tight_layout=True)
        
        # Connect "scrolling the wheel" to its task
        self.fig.canvas.mpl_connect('scroll_event', self) # Connecting it to just "self" will go inside the method __call__
        # Connect "Clicking in the figure" to its task
        self.cid = self.fig.canvas.mpl_connect('button_press_event', self) # Connecting it to just "self" will go inside the method __call__
        
        # Show the masterpiece
        self.update()
        self.fig.show()
        
        return 
    
    def __call__(self,event):
        """
        event generated by mouse clicks or anything else. 
        """     
        self.event = event
        if (event.name=='button_press_event') and event.dblclick:
            """
            When the user double click, show the times with a vertical bar
            Only do it for double click. Otherwise it's hard to distinguish with other
            manipulation of the plot            
            """
            _debug('%s click: button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %
                  ('double' if event.dblclick else 'single', event.button,
                   event.x, event.y, event.xdata, event.ydata))            
            #Increment the number of line shown
            self.nbLines += 1 
            
            if self.nbLines >=2:
                # If there is more than two lines, 
                # Note the last x position before overiding it
                self.xprev = self.xpos
                
            #get the positions for plotting the line
            self.xpos = event.xdata
            ymin = 0
            ymax = self.ax.dataLim.height
            #Plot the line and the label
            self.ax.plot([self.xpos, self.xpos], [ymin, ymax], 'k--', 
                         label='x%d=%f'%(self.nbLines, self.xpos))
            self.ax.text(self.xpos, ymax, 'x%d'%self.nbLines)
            self.ax.legend()


            if self.nbLines >=2:
                # If there is more than two lines, 
                # show the differences between the two lasts
                self.dx = self.xpos - self.xprev  
                self.title_str += '\nx%d - x%d = %f'%(self.nbLines, self.nbLines-1, self.dx)
            self.ax.set_title(self.title_str)

            #The following update the plot. 
            self.fig.canvas.draw_idle()  
            
        if event.name=='scroll_event':
            self.onscroll(event)
            
    def onscroll(self, event):
        """
        What to do when the mouse-wheel is scrolled
        """
        _debug("%s %s" % (event.button, event.step))
        
        
        
        if event.button == 'up':
            self.ind_block = (self.ind_block + 1) % self.nb_block
        else:
            self.ind_block = (self.ind_block - 1) % self.nb_block
        self.update()      
        
    def update(self):
        """
        Update the plot
        
        """
        self.nbLines = 0 #Reinitialize the number of lines
        
        # Clean the graph before reputting the stuffs
        self.ax.cla() 
        self.plot_pulse_pattern(self.block_s[self.ind_block], self.ax)
          
        # Set the title
        self.sequence_name = self.pulse_sequence.get_name()
        
        self.title_str = (self.sequence_name+' Block %d/%d'%(self.ind_block+1,self.nb_block)
                          +'\nDouble click for getting time'
                          +'\nScroll to change block')
            
        self.ax.set_title(self.title_str)

            
        
        #The following update the plot. 
        self.fig.canvas.draw_idle()  
        
    def plot_pulse_pattern(self, pulse_block, ax):
        """
        Plot the user-input pulsePatternBlock. 
        
        pulse_block:
            PulsePatternBlock object to plot
        
        """
        tickDuration = pulse_block.tickDuration
        pattern = pulse_block.get_pulse_pattern()
        
        
        for i, channelPulses in enumerate(pattern):
            #Extract the information
            DIO = channelPulses.get_channel()
            name = channelPulses.get_name()
            times_tick = channelPulses.get_pulses_tick()
            #Add the 0 to the time for clarity in the plot   
            times = np.append(0, tickDuration*times_tick)
            
            # Extract the states "Up" and "down" by noticing that the first tick correspond to a raise, the second to a fall, the third to a raise, etc. 
            y = np.array([])
            for ii in range(int(len(times_tick)/2)):
                #Loop over half the size of the ticks. 
                y = np.append(y, [1, 0])   
            # Add the 0 to the state for clarity in the plot    
            states = np.append(0, y)
            _debug(i, DIO, states+2*i)
            # Plot it
            plt.step(times, states+2*i, where='post', color='C%d'%i)
            plt.text(0, 2*i+0.35, name, color='C%d'%i)
            plt.text(0, 2*i+0.15, 'Channel %d'%DIO, color='C%d'%i)
            
        plt.xlabel('Time (us)')
        ax.spines['left' ].set_visible(False) # Remove left line
        ax.spines['right'].set_visible(False) # Remove right line
        ax.spines['top'  ].set_visible(False) # Remove top line
        plt.yticks([])
        pattern_name = pulse_block.get_name()
        plt.title(pattern_name+'\nNote that zero is not included in the real pulse instruction') 
        
        return ax
    
    
 


class CoolSequence():
    """
    Define some sequence for quick access.  
    """
    def __init__(self, model):
        """
        Input:
            model
            What sequence to output
        """
        if model == '1':
            self.sequence = self.sequence_test1()
        if model == 'pulse2':
            self.sequence = self.sequence_test2()    
        if model == 'read1':
            self.sequence = self.sequence_readtest1() 
        if model == 'read2':
            self.sequence = self.sequence_readtest2() 
        if model == 'rabi_fake':
            self.sequence = self.sequence_rabi_fake()
        if model == 'rabi_fake_clean':
            self.sequence = self.sequence_rabi_fake_clean()
            
    def get_sequence(self):
        """
        Return the sequence
        """
        return self.sequence
        
    def sequence_test1(self):
        """
        Create a funny sequence, for quick test and checkup 
        """
        # Create some channel pulse 
        laser = ChannelPulses(channel=2, name='Laser cool')
        laser.add_pulses([100,120,360,500])
        laser.add_pulses([580, 600])
        # Create some channel pulse 
        RF = ChannelPulses(channel=3, name='Super RF')
        RF.add_pulses([150,250.5])
        RF.add_trainPulses(300, 10,30, 10)
        # Create some channel pulse 
        trig = ChannelPulses(channel=7, name='Wonderful Trigger')
        trig.add_pulses([800,850])
        # Create a pulse pattern block
        rabi_step1 = PulsePatternBlock(name='Rabi step1')
        rabi_step1.add_channelEvents(laser)
        rabi_step1.add_channelEvents(RF)
        rabi_step1.add_channelEvents(trig)    
        
        # Create some channel pulse  
        laser = ChannelPulses(channel=2, name='Laser cool')
        laser.add_pulses([100,120,360,500])
        laser.add_pulses([580, 600])
        # Create some channel pulse 
        RF = ChannelPulses(channel=3, name='Super RF')
        RF.add_pulses([150,250.5])
        RF.add_trainPulses(260, 10,30, 10)
        # Create some channel pulse 
        trig = ChannelPulses(channel=7, name='Wonderful Trigger')
        trig.add_pulses([700, 720])
        # Create a pulse pattern block
        rabi_step2 = PulsePatternBlock(name='Rabi step2')
        rabi_step2.add_channelEvents(laser)
        rabi_step2.add_channelEvents(RF)
        rabi_step2.add_channelEvents(trig)   
        
        # Create a sequence of block
        rabi = Sequence(name='Rabi chill')
        rabi.add_block(rabi_step1)
        rabi.add_block(rabi_step2)
        
        return rabi
    
    def sequence_test2(self):
        """
        Create a sequence with a pulse shifted on each block.
        """
        # All time are in us
        t1_laser = 100 # First time to turn ON the laser
        t2_laser = 650 # Last time to turn ON the laser
        dt_laser = 30  # Pulse duration of the laser 
        dt_trig = 10 # Duration of the pulse for the trigger
        dt_pulse = 10 # Width of the RF pulse
        Ntime = 5 # Number of time the RF pulse is shifted (this defines the number of blocks within the sequence )
        
        # Define raise time of the RF pulse
        tmin = t1_laser + 2*dt_laser
        tmax = t2_laser - 2*dt_laser
        tlin    = np.linspace(tmin, tmax, Ntime)  #Linear spacing
        # Transform it to a log scale
        beta  = 4/(tmax-tmin) # Factor for the logaritmic spacing (how squeezed will be the point near tmin) 
        B_log = (tmax-tmin)/(np.exp(beta*tmax)-np.exp(beta*tmin))
        A_log = tmin - B_log*np.exp(beta*tmin) 
        # The following is the list of all initial time for the pulse
        t0_pulse_s = A_log + B_log*np.exp(beta*tlin)  #Lograritmic spacing   

        #Initialize the sequence
        T1_sequence = Sequence(name='T1 sequence')        
        
        # The channel laser and trigger never change in each block, so we 
        # define them outside of the loop.
        # Channel pulse for the laser
        laser = ChannelPulses(channel=2, name='Laser nice')
        laser.add_pulses([t1_laser,t1_laser+dt_laser,
                          t2_laser,t2_laser+dt_laser])
        # Channel pulse for the trigger
        trig = ChannelPulses(channel=7, name='Wonderful Trigger')
        trig.add_pulses([t2_laser+dt_laser, t2_laser+dt_laser+dt_trig]) 
        # Create a block of pulse pattern for each raise time of the RF pulse
        for i, t0_pulse in enumerate(t0_pulse_s):
           # Channel pulse for the RF
           RF = ChannelPulses(channel=3, name='Super RF')
           RF.add_pulses([t0_pulse, t0_pulse+dt_pulse])
           # Create the block of pulse pattern
           T1_block = PulsePatternBlock(name='T1 block %d'%i)
           T1_block.add_channelEvents([laser, RF, trig])
           # Add this block in the sequence
           T1_sequence.add_block(T1_block)
        
        return T1_sequence
    
    def sequence_readtest1(self):
        """
        Create a train of pulse and count them with a single block. 
        """
        # Create a Channel pulse for the train of pulse
        train = ChannelPulses(channel=6, name='Tchou Tchou')
        train.add_trainPulses(0, 20,20, 20)
        
        # Create a Channel for reading the counts
        read = ChannelPulses(channel=1, name='read')
        read.add_pulses([30,550, 600,670])
        
        #Create the block
        block = PulsePatternBlock(name='Block read')
        block.add_channelEvents([read, train])
        
        #Create the sequence
        reading_seq = Sequence('Reading sequence')
        reading_seq.add_block(block)
        
        return reading_seq

    def sequence_readtest2(self):
        """
        Create a train of pulse and count them with many blocks, each with 
        different number of counts. 
        """

        #Create the sequence that we gonna feed with blocks
        reading_seq = Sequence('Reading sequence')
        
        # Create a Channel pulse for the train of pulse
        train = ChannelPulses(channel=6, name='Tchou Tchou')
        train.add_trainPulses(0, 20,20, 20)
        
        dt_read1 = np.linspace(50, 550, 4)
        
        for i, dt in enumerate(dt_read1):
            # Create a Channel for reading the counts
            read = ChannelPulses(channel=1, name='read')
            read.add_pulses([30,30+dt, 600,670])
            
            #Create the block
            block = PulsePatternBlock(name='Block read %d'%i)
            block.add_channelEvents([read, train])
            
            # Add the block to the sequence
            reading_seq.add_block(block)
        
        return reading_seq
    
    def sequence_rabi_fake(self):
        """
        Create fake Rabi oscillation.
        
        There is two readout per block:
            The Rabi oscillation and the reference counts
        """
        
         # In our experiment, the following is 0.1
        PLr0 = 0.1 # Photoluminescence rate (count/us) of state |0>
        C = 0.8 # Contrast
        dt_readout = 10 # Readout time (us)
        PC_ms0 = PLr0*dt_readout # Expected photocounts of state |0>
        PC_ms1 = PC_ms0*(1-C) # Expected photocounts of state |0>
        
        dt_RF_s = np.linspace(0, 1000, 40) # Intervals of time for the RF
        omega = 2*2*np.pi/dt_RF_s[-1] # Rabi frequence
        fake_count_s = (PC_ms0-PC_ms1)/2*np.cos(omega*dt_RF_s) + (PC_ms0+PC_ms1)/2 # Expected counts
        ref_counts_s = dt_RF_s*0 + PC_ms0 # Reference counts
        
        t0_ref = 100 #Time for the reference
        t0_RF = t0_ref + dt_readout+10 # Initial raise time for the RF
        t0_readout_s = t0_RF+dt_RF_s # Time to readout
        t0_trigger = t0_readout_s[-1]+dt_readout # Time for the trigger pulse
        
        # Initiate the sequence on which we gonna construct the Rabi sequence
        sequence = Sequence(name='Rabi sequence')
        # Create a channel for the trigger
        trigger = ChannelPulses(channel=7, name='Trigger')
        trigger.add_pulses([t0_trigger, t0_trigger+100])
        # Create a block for each time interval for the RF-pulse
        for i, dt_RF in enumerate(dt_RF_s):
            # Channel pulse for the RF
            RF = ChannelPulses(channel=3, name='RF')
            RF.add_pulses([t0_RF, t0_RF+dt_RF])            
            # Create the ChannePulse for the readout
            read = ChannelPulses(channel=1, name='Read') 
            
            # Read the Reference
            read.add_pulses([t0_ref,t0_ref+ dt_readout])
            # Generate a fake photcounter
            # Create a channel for the fake PC
            photocounter = ChannelPulses(channel=6, name='Fake photcounter')
            PC = np.random.poisson(ref_counts_s[i]) # Number of counts (poissonian)
            # Create the pulse train only if the count exist. 
            if PC>0:
                a = 0.5 # Proportion of the span of the fake pulse during the readout time
                T = a*dt_readout/(2*PC) # ON and OFF time interval for the fake pulse
                photocounter.add_trainPulses(t0_ref+T,T,T,PC) 
                
            # Read the Rabi oscillation
            read.add_pulses([t0_readout_s[i], t0_readout_s[i] + dt_readout])
            # Generate a fake photcounter
            PC = np.random.poisson(fake_count_s[i]) # Number of counts (poissonian)
            # Create the pulse train only if the count exist. 
            if PC>0:
                a = 0.5 # Proportion of the span of the fake pulse during the readout time
                T = a*dt_readout/(2*PC) # ON and OFF time interval for the fake pulse
                photocounter.add_trainPulses(t0_readout_s[i]+T,T,T,PC)  
                
            # Build the block
            block = PulsePatternBlock(name='Block Rabi RF = %.2f us'%dt_RF)
            block.add_channelEvents([RF, read, photocounter, trigger])
            # Add the block to the sequence
            sequence.add_block(block)
        
        return sequence

    def sequence_rabi_fake_clean(self):
        """
        Create fake Rabi oscillation with no noise. 
        This is in order to have well defined count for debugging
        
        There is two readout per block:
            The Rabi oscillation and the reference counts
        """
         # In our experiment, the following is 0.1
        PLr0 = 0.1 # Photoluminescence rate (count/us) of state |0>
        C = 0.8 # Contrast
        dt_readout = 10 # Readout time (us)
        PC_ms0 = 20*PLr0*dt_readout # Expected photocounts of state |0>
        PC_ms1 = PC_ms0*(1-C) # Expected photocounts of state |0>
        
        dt_RF_s = np.linspace(0, 1000, 40) # Intervals of time for the RF
        omega = 2*2*np.pi/dt_RF_s[-1] # Rabi frequence
        fake_count_s = (PC_ms0-PC_ms1)/2*np.cos(omega*dt_RF_s) + (PC_ms0+PC_ms1)/2 # Expected counts
        ref_counts_s = dt_RF_s*0 + PC_ms0 # Reference counts
              
        t0_RF = dt_readout+10 # Initial raise time for the RF
        t0_readout_s = t0_RF+dt_RF_s # Time to readout
        t0_trigger = t0_readout_s[-1]+dt_readout # Time for the trigger pulse
        
        # Initiate the sequence on which we gonna construct the Rabi sequence
        sequence = Sequence(name='Rabi sequence')
        # Create a channel for the trigger
        trigger = ChannelPulses(channel=7, name='Trigger')
        trigger.add_pulses([t0_trigger, t0_trigger+100])
        # Create a block for each time interval for the RF-pulse
        for i, dt_RF in enumerate(dt_RF_s):
            # Channel pulse for the RF
            RF = ChannelPulses(channel=3, name='RF')
            RF.add_pulses([t0_RF, t0_RF+dt_RF])            
            # Create the ChannePulse for the readout
            read = ChannelPulses(channel=1, name='Read') 
            
            # Read the Reference
            read.add_pulses([0.2, dt_readout])
            # Generate a fake photcounter
            # Create a channel for the fake PC
            photocounter = ChannelPulses(channel=6, name='Fake photcounter')
            PC = int(ref_counts_s[i]) # Number of counts (poissonian)
            # Create the pulse train only if the count exist. 
            if PC>0:
                a = 0.5 # Proportion of the span of the fake pulse during the readout time
                T = a*dt_readout/(2*PC) # ON and OFF time interval for the fake pulse
                photocounter.add_trainPulses(0+T,T,T,PC) 
                
            # Read the Rabi oscillation
            read.add_pulses([t0_readout_s[i], t0_readout_s[i] + dt_readout])
            # Generate a fake photcounter
            PC = int(fake_count_s[i]) # Number of counts (poissonian)
            # Create the pulse train only if the count exist. 
            if PC>0:
                a = 0.5 # Proportion of the span of the fake pulse during the readout time
                T = a*dt_readout/(2*PC) # ON and OFF time interval for the fake pulse
                photocounter.add_trainPulses(t0_readout_s[i]+T,T,T,PC)  
                
            # Build the block
            block = PulsePatternBlock(name='Block Rabi RF = %.2f us'%dt_RF)
            block.add_channelEvents([RF, read, photocounter, trigger])
            # Add the block to the sequence
            sequence.add_block(block)
        
        return sequence




if __name__=="__main__":
    _debug_enabled = True
    
#    sequence = CoolSequence(model='read2').get_sequence()
#    
#    print()
#    print('Sequence ', sequence.get_name())
#    for block in sequence.get_block_s():
#        print()
#        print('Pulse pattern block', block.get_name())
#        for cp in block.get_pulse_pattern():
#            print(cp.get_name(), ' at channel ',cp.get_channel()) 
#            
#    # Check with the gui
#    gui = GUIPulsePattern(sequence) 
#    
#    # Test the delay functions
#    new_sequence = add_raise_delays(sequence, DIOs=[3,6], delays=[100,50])
#    new_sequence = add_fall_delays(new_sequence, DIOs=[3,6], delays=[200,50])
#    
#    # Check it
#    gui_new = GUIPulsePattern(new_sequence)
    
    
    # Verify some pulse sequence
    from gui_pulser import GUIT1TimeTrace3 as gui_seq
    thegui = gui_seq()
    thegui.button_prepare_experiment_clicked()
    sequence = thegui.sequence
    self = GUIPulsePattern(sequence) 
    
    
    
    
    
    
    
    








