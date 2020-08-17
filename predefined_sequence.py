# -*- coding: utf-8 -*-
"""
Created on Wed May 27 16:29:48 2020

Implement predefined pulse sequences

@author: Michael
"""


import numpy as np
from pulses import ChannelPulses, PulsePatternBlock, Sequence


# Debug stuff.
_debug_enabled = False

def _debug(*a):
    if _debug_enabled: 
        s = []
        for x in a: s.append(str(x))
        print(', '.join(s))


class PredefinedSequence():
    """
    Define some sequence for quick access.  
    """
    def __init__(self):
        """
        Input:
            model
            What sequence to output
        """
        
        # Contain all existing sequence
        self.sequence_list = ['pulse_simple','read_simple','rabi_fake',
                              'rabi_fake_clean', 'T1_3_readout', 'slow_trigger',
                              'ESR', 'Rabi'] 
   
    def get_sequence_list(self):
        """
        Return the list of existing sequence 
        """
        return self.sequence_list
            
    def get_sequence(self, model):
        """
        Return the sequence
        """
        if model == 'pulse_simple':
            return self.pulse_simple()    
        if model == 'read_simple':
            return self.read_simple()
        if model == 'rabi_fake':
            return self.rabi_fake()
        if model == 'rabi_fake_clean':
            return self.rabi_fake_clean()    
        if model == 'T1_3_readout':
            return self.T1_3_readout()      
        if model == 'slow_trigger':
            return self.slow_trigger()
        if model == 'ESR':
            return self.ESR()
        if model == 'Rabi':
            return self.Rabi()        
        
        return self.sequence
    
    def pulse_simple(self):
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

    def read_simple(self):
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
    
    def rabi_fake(self):
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

    def rabi_fake_clean(self):
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
    
    def T1_3_readout(self):
        """
        Define a pulse sequence for the T1 measurement. Basically a T1 measure. 
        For a single sequence, measure the three states. 
        """
        
         # In our experiment, the following is 0.1
        PLr0 = 0.1 # Photoluminescence rate (count/us) of state |0>
        C = 0.8 # Contrast
        dt_readout = 10 # Readout time (us)
        Gp = 15*1e-3 # Rate (MHz)
        Gm = 31*1e-3 # Rate (MHz)
        PC_ms0 = PLr0*dt_readout # Expected photocounts of state |0>
        
        Ntime = 20 # Number of times to probes
        
        # Define probing times, relative to the initialization
        tmin = 0.1/(Gp+Gm+np.sqrt(Gm**2 - Gp*Gm + Gp**2)) # us
        tmax = 3/(Gp+Gm+np.sqrt(Gm**2 - Gp*Gm + Gp**2)) # us
        _debug('tmin:',tmin)
        _debug('tmax:',tmax)
#        tlin    = np.linspace(tmin, tmax, Ntime)  #Linear spacing
#        # Transform it to a log scale
#        beta  = 4/(tmax-tmin) # Factor for the logaritmic spacing (how squeezed will be the point near tmin) 
#        B_log = (tmax-tmin)/(np.exp(beta*tmax)-np.exp(beta*tmin))
#        A_log = tmin - B_log*np.exp(beta*tmin) 
#        # The following is the list of all initial time for the pulse
#        t_probe_s = A_log + B_log*np.exp(beta*tlin)  #Lograritmic spacing  
        t_probe_s = np.linspace(tmin, tmax, Ntime)
        _debug(t_probe_s)
        
        dt_laser = 5 # Interval of time for shining the laser
        

        # Create the number of fake counts
        fun = analytic(PL0 = PC_ms0, C=C)
        count_ms0_s = fun.PLms0 (t_probe_s, Gp, Gm) 
        count_msp_s = fun.PLmsP1(t_probe_s, Gp, Gm) 
        count_msm_s = fun.PLmsM1(t_probe_s, Gp, Gm) 

        # Initiate the sequence on which we gonna construct the Rabi sequence
        sequence = Sequence(name='T1 3 readout')

        # Create a channel for the trigger
        t0_trigger = 3*(tmax+dt_laser+40)+10
        trigger = ChannelPulses(channel=7, name='Trigger')
        trigger.add_pulses([t0_trigger, t0_trigger+10])  
        
        # Create a block for each time to probe
        for i in range(len(t_probe_s)):
            t_probe = t_probe_s[i]
            
            # Each block will consist of three step: read ms0, 1 and -1
            
            # Laser channel for each ms state
            laser = ChannelPulses(channel=2, name='Laser')      
            # Read channel for each state
            read  = ChannelPulses(channel=1, name='Read')
            # Channel for generating fake photocounts 
            NV_PL = ChannelPulses(channel=6, name='Photoluminescence')
            # Channel for the Pi-pulse initializing ms=+-1
            RF    = ChannelPulses(channel=3, name='RF')
           
            # Prepare and read ms=0
            # Prepare the state
            laser.add_pulses([0.5, 0.5+dt_laser])
            # Let evolve the state and read it
            tref = laser.get_pulses_times()[-1] # When the laser end up to initialize the state
            read.add_pulses([tref+t_probe, tref+t_probe +dt_readout])
            # Create the fake photocount
            PC = np.random.poisson(count_ms0_s[i]) # Number of counts (poissonian)
            # Create the pulse train only if the count exist. 
            if PC>0:
                a = 0.5 # Proportion of the span of the fake pulse during the readout time
                T = a*dt_readout/(2*PC) # ON and OFF time interval for the fake pulse
                NV_PL.add_trainPulses(tref+t_probe+T,T,T,PC)         
                
            # Prepare and read ms=+1
            # Note the overall shift
            t_shift = tmax+dt_laser+20 # When to start the new measurement
            _debug('t_shift',t_shift)
            # Prepare the state
            laser.add_pulses([t_shift+0.5, t_shift+0.5+dt_laser]) # Initialise in ms=0
            tref_RF = laser.get_pulses_times()[-1]+10
            RF.add_pulses([tref_RF,tref_RF+10]) # Flip in ms=-1
            # Let evolve the state and read it
            tref = RF.get_pulses_times()[-1] # When the laser end up to initialize the state
            read.add_pulses([tref+t_probe, tref+t_probe +dt_readout])
            # Create the fake photocount
            PC = np.random.poisson(count_msp_s[i]) # Number of counts (poissonian)
            # Create the pulse train only if the count exist. 
            if PC>0:
                a = 0.5 # Proportion of the span of the fake pulse during the readout time
                T = a*dt_readout/(2*PC) # ON and OFF time interval for the fake pulse
                tref = read.get_pulses_times()[-1]-dt_readout
                NV_PL.add_trainPulses(tref+T,T,T,PC)  

            # Prepare and read ms=-1
            # Note the overall shift
            t_shift = 2*(tmax+dt_laser+10)+20 # When to start the new measurement
            _debug('t_shift',t_shift)
            # Prepare the state
            laser.add_pulses([t_shift+0.5, t_shift+0.5+dt_laser]) # Initialise in ms=0
            tref_RF = laser.get_pulses_times()[-1]+10
            RF.add_pulses([tref_RF,tref_RF+10]) # Flip in ms=-1
            # Let evolve the state and read it
            tref = RF.get_pulses_times()[-1] # When the laser end up to initialize the state
            read.add_pulses([tref+t_probe, tref+t_probe +dt_readout])
            # Create the fake photocount
            PC = np.random.poisson(count_msm_s[i]) # Number of counts (poissonian)
            # Create the pulse train only if the count exist. 
            if PC>0:
                a = 0.5 # Proportion of the span of the fake pulse during the readout time
                T = a*dt_readout/(2*PC) # ON and OFF time interval for the fake pulse
                tref = read.get_pulses_times()[-1]-dt_readout
                NV_PL.add_trainPulses(tref+T,T,T,PC)              

            _debug('t_probe', t_probe)
            # Add all that masterpiece to a block
            block = PulsePatternBlock(name='Block tprobe = %.2f us'%t_probe)
            block.add_channelEvents([laser, RF, read, NV_PL, trigger])
            # Add the block to the sequence
            sequence.add_block(block)                  
        return sequence


    def slow_trigger(self):
        """
        Pulse the trigger slowly enought to be able to see some changes
        on the oscilloscope. 
        
        That's a first step for building a pulse sequence for ESR
        
        """
        # Initiate the sequence on which we gonna construct the Rabi sequence
        sequence = Sequence(name='Slow trigger')
        
        # Create a channel for the trigger
        channel_trigger = ChannelPulses(channel=7, name='Trigger')
        t0_trigger = 50*1e3 # us 
        channel_trigger.add_pulses([t0_trigger, t0_trigger+100])

        # Create the ChannePulse for the readout
        channel_read = ChannelPulses(channel=1, name='Read')      
        channel_read.add_pulses([0.1*t0_trigger, 0.8*t0_trigger])
        
        # Create many block of the same thing. 
        N_block = 4
        for i in range(N_block):
            # Build the block
            block = PulsePatternBlock(name='Block %d'%i)
            block.add_channelEvents([channel_read, channel_trigger])
            # Add the block to the sequence
            sequence.add_block(block)
        
        return sequence
    
    def ESR(self):
        """
        THe base for an ESR. 
        
        """
        # Initiate the sequence on which we gonna construct the Rabi sequence
        sequence = Sequence(name='Slow trigger')
        
        t0_read = 5000  # Start time to read (us)
        t1_read = 10000 # Stop time to read (us)
        
        # Create a channel for the trigger
        channel_trigger_RF = ChannelPulses(channel=7, name='Change Frequency')
        channel_trigger_RF.add_pulses([t1_read+1, t1_read+100])

        # Create the ChannePulse for when to read
        channel_read = ChannelPulses(channel=1, name='Read')      
        channel_read.add_pulses([t0_read, t1_read])

        # A Channel for the modulation of the pulse
        channel_PM = ChannelPulses(channel=3, name='Pulse modulation')      
        channel_PM.add_pulses([t0_read, t1_read])
        
        # Create the ChannePulse for the laser output
        channel_laser = ChannelPulses(channel=2, name='Laser')      
        channel_laser.add_pulses([t0_read-500 , t1_read])   
        
        # Create a channel for the end state (use full for the scope)
        channel_sync = ChannelPulses(channel=5, name='Synchronize scope')
        channel_sync.add_pulses([t1_read+1, t1_read+100]) # Same as trigger
        
        # Create many block of the same thing. 
        N_block = 200
        for i in range(N_block):
            # Build the block
            block = PulsePatternBlock(name='Block %d'%i)
            block.add_channelEvents([channel_read, 
                                     channel_trigger_RF, 
                                     channel_laser,
                                     channel_PM,
                                     channel_sync])
            # Add the block to the sequence
            sequence.add_block(block)
        
        return sequence
    
    def Rabi(self):
        """
        Create a rabi measurement
        
        There is two readout per block:
            The Rabi oscillation and the reference counts
        """
        T_max_us = 1 # Maximum time 
        N_block = 50 # Number of point to take
        dt_readout = 0.4 # Readout time (us)
        
        t0_ref = 0.1 #Initial time for the reference
        t0_RF = t0_ref + 2*dt_readout # Initial raise time for the RF
        
        delay_laser = 0.05 # Delay (us) that we send the laser before the readout
        
        
        # Define the time durations of the RF
        dt_s = np.linspace(0, T_max_us, N_block)
        
        # Initiate the sequence on which we gonna construct the Rabi sequence
        sequence = Sequence(name='Rabi sequence')        
        
        # Initiate the channels
        
        # Create a channel for synching the scope
        channel_sync = ChannelPulses(channel=5, name='Sync with scope')
        channel_sync.add_pulses([0, 0.5]) # At the beggining
        

        # Define a block for each duration to probe
        for i, dt in enumerate(dt_s):

            # Channel for the modulatiion of the RF
            channel_RF_mod = ChannelPulses(channel=3, name='RF modulation')
            # The RF span from time zero to the duration
            channel_RF_mod.add_pulses([t0_RF, t0_RF+dt])
            
            # Channel for the readout
            channel_read = ChannelPulses(channel=1, name='Read') 
            # Add a pulse for the reference
            channel_read.add_pulses([t0_ref,t0_ref+ dt_readout, ])
            # Add a pulse for the readout after the RF
            t_read = t0_RF+dt
            channel_read.add_pulses([t_read, t_read+ dt_readout, ])
            
            # Channel for the laser output, which follows the readout
            channel_laser = ChannelPulses(channel=2, name='Laser') 
            # Add a pulse for the reference
            channel_laser.add_pulses([t0_ref-delay_laser,t0_ref+ dt_readout, ])
            # Add a pulse for the readout after the RF
            t_read = t0_RF+dt
            channel_laser.add_pulses([t_read-delay_laser, t_read+ dt_readout, ])            

            # Build the block
            block = PulsePatternBlock(name='Block Rabi RF = %.2f us'%dt)
            block.add_channelEvents([channel_sync,
                                     channel_RF_mod,
                                     channel_read ,
                                     channel_laser])
            # Add the block to the sequence
            sequence.add_block(block)
        
        return sequence            

            
class analytic():
    """
    Define the analytic form of known functions related to the decay of the 
    three levels. 
    These analytic function are useful for performing the simulation and to 
    compute some numerical derivatives. 
    """

    def __init__(self, PL0=0.04, C=0.2, dGp=0.001, dGm=0.001):
        """
        PL0 is the photoluminescence of the state |0> at t=0
        C is the contrast, defined such that the photoluminescence of |1> is
                           PL0*(1-C)
        """
        self.PL0 = PL0
        self.C = C
        
        #Set the infinitesimal step for the derivatives
        self.dGp = dGp
        self.dGm = dGm    
        
    def PLms0(self, t, Gp, Gm):
        """
        Analytic solution for the photoluminescence when the 
        state is initialized in ms=0 
        t: time to check
        Gp: gamma+
        Gm: gamma-
        """
        PL0 = self.PL0
        C   = self.C
        A   = PL0*(1-C*2/3)  
        
        G0 = np.sqrt(Gm**2 - Gp*Gm + Gp**2)
        
        B = (PL0*C/(6*G0))*(2*G0+Gp+Gm)
        CC = (PL0*C/(6*G0))*(2*G0-Gp-Gm)
        
        betap = Gp + Gm + G0
        betam = Gp + Gm - G0
        
        return A + B*np.exp(-betap*t) + CC*np.exp(-betam*t)
    
    def PLmsP1(self, t, Gp, Gm):
        """
        Analytic solution for the photoluminescence when the 
        state is initialized in ms=+1 
        t: time to check
        Gp: gamma+
        Gm: gamma-
        """
        PL0 = self.PL0
        C   = self.C
        A   = PL0*(1-C*2/3)  
        G0 = np.sqrt(Gm**2 - Gp*Gm + Gp**2)
        
        E = -(PL0*C/(6*G0))*(G0+2*Gp-Gm)
        F = -(PL0*C/(6*G0))*(G0-2*Gp+Gm)
        
        betap = Gp + Gm + G0
        betam = Gp + Gm - G0
        
        return A + E*np.exp(-betap*t) + F*np.exp(-betam*t)
    
    def PLmsM1(self, t, Gp, Gm):
        """
        Analytic solution for the photoluminescence when the 
        state is initialized in ms=-1 
        t: time to check
        Gp: gamma+
        Gm: gamma-
        """
        PL0 = self.PL0
        C   = self.C
        A   = PL0*(1-C*2/3)  
        G0 = np.sqrt(Gm**2 - Gp*Gm + Gp**2)
        
        E = -(PL0*C/(6*G0))*(G0+2*Gm-Gp)
        F = -(PL0*C/(6*G0))*(G0-2*Gm+Gp)
        
        betap = Gp + Gm + G0
        betam = Gp + Gm - G0
        
        return A + E*np.exp(-betap*t) + F*np.exp(-betam*t)    

    def diff_P(self, t, Gp, Gm):
        """
        Difference of the photuminescence for the ms=0 and ms=+1 measurements.
        t: time to check
        Gp: gamma+
        Gm: gamma-
        """
        PL0 = self.PL0
        C   = self.C
        G0 = np.sqrt(Gm**2 - Gp*Gm + Gp**2)
        
        betap = Gp + Gm + G0
        betam = Gp + Gm - G0
        
        return (C*PL0/(2*G0))*( (G0+Gp)*np.exp(-betap*t) + (G0-Gp)*np.exp(-betam*t) )
        
    def diff_M(self, t, Gp, Gm):
        """
        Difference of the photuminescence for the ms=0 and ms=-1 measurements.
        t: time to check
        Gp: gamma+
        Gm: gamma-
        """
        PL0 = self.PL0
        C   = self.C
        G0 = np.sqrt(Gm**2 - Gp*Gm + Gp**2)
        
        betap = Gp + Gm + G0
        betam = Gp + Gm - G0
        
        return (C*PL0/(2*G0))*( (G0+Gm)*np.exp(-betap*t) + (G0-Gm)*np.exp(-betam*t) )       

    def ddiffpdGp(self, t_measure, Gp, Gm, dGp):
        """
        Numerical derivative of diff_P with respect to Gp. 
        Same parameter as diff_P. 
        dGp is the step in gamma+ for the derivative
        """
        f1 = self.diff_P(t_measure, Gp+dGp, Gm)
        f0 = self.diff_P(t_measure, Gp    , Gm)
        return (f1-f0)/dGp
    
    def ddiffpdGm(self, t_measure, Gp, Gm, dGm):
        """
        Numerical derivative of diff_P with respect to Gm. 
        Same parameter as diff_P. 
        dGm is the step in gamma- for the derivative
        """
        f1 = self.diff_P(t_measure, Gp, Gm+dGm)
        f0 = self.diff_P(t_measure, Gp, Gm    )
        return (f1-f0)/dGm
    
    def ddiffmdGp(self, t_measure, Gp, Gm, dGp):
        """
        Numerical derivative of diff_M with respect to Gp. 
        Same parameter as diff_M. 
        dGp is the step in gamma+ for the derivative
        """
        f1 = self.diff_M(t_measure, Gp+dGp, Gm)
        f0 = self.diff_M(t_measure, Gp    , Gm)
        return (f1-f0)/dGp
    
    def ddiffmdGm(self, t_measure, Gp, Gm, dGm):
        """
        Numerical derivative of diff_M with respect to Gm. 
        Same parameter as diff_M. 
        dGm is the step in gamma- for the derivative
        """
        f1 = self.diff_M(t_measure, Gp, Gm+dGm)
        f0 = self.diff_M(t_measure, Gp, Gm    )
        return (f1-f0)/dGm    

    def eRates(self, Gp, Gm, eDiffp, eDiffm, corrDiffpm,  tp, tm):
        """
        Get the error in the rates from the error in the measured difference in PL,
        and the correlation in the difference. 
        Basically, the idea is to inverse the derivative of the analytic form for 
        the difference. 
        Assume a correlation between the two difference. If there is no 
        correlation, set corrDiffpm to zero.
        
        The function also return the correlation :D
        
        Gp,Gm: rates gamma+- that the NewtonRaphson found
        eDiffp, eDiffm: Error in the differences from the experiment.
        corrDiffpm: correlation between the two difference
        tp, tm: times at which the diffp and diffm is measured       
        """
        #For now we take the derivative of the function fp and fm, because the 
        #measured difference doesn't change anything in the derivative. So we put 
        #zero for the measured difference in the functions.
        
        eDiffp_2 = eDiffp*eDiffp
        eDiffm_2 = eDiffm*eDiffm
        
        #Error in gamma+, including the correlation
        ap = 1/self.ddiffpdGp(tp, Gp, Gm, self.dGp)
        bp = 1/self.ddiffmdGp(tm, Gp, Gm, self.dGp)
        eGp = np.sqrt( eDiffp_2*ap**2 + eDiffm_2*bp**2 + 2*ap*bp*corrDiffpm )
    
        #Error in gamma-, including the correlation
        am = 1/self.ddiffpdGm(tp, Gp, Gm, self.dGm)
        bm = 1/self.ddiffmdGm(tm, Gp, Gm, self.dGm)
        eGm = np.sqrt( eDiffp_2*am**2 + eDiffm_2*bm**2 + 2*am*bm*corrDiffpm )    
        
        #Correlation between gamma+ and gamma-
        corrGpm  = (ap*am*eDiffp_2 + bp*bm*eDiffm_2 +
                    (ap*bm + am*bp)*corrDiffpm )
        
        return (eGp, eGm, corrGpm)    
    
    
    def sensitivity_4measurements(self,tp, tm, t_ps_0, t_ps_pm,  Gp, Gm, R=1e4):
        """
        Return the expected sensitivity if you are to measure at time tp and
        tm over and over (with the HitOn protocol). 
        
        tp: probing time at whicht the difference + is measured. 
        tm: probing time at whicht the difference - is measured. 
        t_ps_0: time duration of the pulse sequence for the measurement of ms=0 NOT INCLUDING THE PROBING TIME
        t_ps_pm: time duration of the pulse sequence for the measurement of ms=+-1 NOT INCLUDING THE PROBING TIME
        R: number of readout performed. (Note that the sensitivity should 
            be independant of the number of readout when it is large enought
            to distinguish the states. It is included here for consistency of 
            the maths and to ease the code)
        Gp: gamma+
        Gm: gamma-        
        """
        
        #Total time for probing
        tTotal = 2*(t_ps_0 + t_ps_pm + tp + tm)* R 
        
        #Uncertainty in the differences
        eDiffp = np.sqrt( (self.PLms0(tp, Gp, Gm) + self.PLmsP1(tp, Gp, Gm) )/R) #Assum poissonian noise in the PL
        eDiffm = np.sqrt( (self.PLms0(tm, Gp, Gm) + self.PLmsM1(tm, Gp, Gm) )/R) #Assum poissonian noise in the PL
        corrDiffpm=0 #No correlation between the measured difference, because at different times
        
        #Uncertainty in the rates, by propagating the uncertainty in the diff into the analytic expression that we have
        eGp, eGm, _ =  self.eRates(Gp, Gm, eDiffp, eDiffm, corrDiffpm,  tp, tm)
        #Sensitivities
        eta_Gp  = eGp*np.sqrt(tTotal)
        eta_Gm  = eGm*np.sqrt(tTotal)
        
        return eta_Gp, eta_Gm            
 
        
        
if __name__=="__main__":
    _debug_enabled = True
    
    from pulses import GUIPulsePattern
    
    seq = PredefinedSequence().get_sequence('ESR')
    gui = GUIPulsePattern(seq)
            
    
    seq = PredefinedSequence().get_sequence('Rabi')
    gui = GUIPulsePattern(seq)    
    
    
    
    
    
    
    
    
    
    
    
    