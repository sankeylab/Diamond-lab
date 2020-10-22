# -*- coding: utf-8 -*-
"""
Created on Thu Oct 15 10:53:53 2020

Goals: Define the api for the signal generators

@author: Childresslab
"""


import numpy       as _n
import spinmob     as _s
import mcphysics   as _mp


# Debug stuff.
_debug_enabled     = False

def _debug(*a):
    if _debug_enabled: 
        s = []
        for x in a: s.append(str(x))
        print(', '.join(s))
        



class signal_generator_api(_mp.visa_tools.visa_api_base):
    """
    General signal generator API base. This will connect and then, based on
    the model number, inherit all the commands from one of the specific model
    classes.
    """
    def __init__(self, name='SMA100B', pyvisa_py=False, simulation=False, timeout=100e3, write_sleep=0.1, **kwargs):
        """
        Visa-based connection to the Anapico signal generator.
        """
        _debug('signal_generator_api.__init__()', pyvisa_py, simulation, timeout, write_sleep)
        
        # Run the core setup.
        _mp.visa_tools.visa_api_base.__init__(self, name, pyvisa_py, simulation, timeout=timeout, write_sleep=write_sleep)
        
        # Inherit the functionality based on the idn
        if self.idn.split(',')[0] in ['AnaPico AG']: 
            _debug('signal_generator_api.__init__() I choose you anapico')
            self._api = anapico_api()
        elif 'SMA100B' in self.idn:
            _debug('signal_generator_api.__init__() I choose you sma100b')
            self._api = sma100b_api()
        elif 'SMB100A' in self.idn:
            _debug('signal_generator_api.__init__() I choose you smb100a')
            self._api = smb100a_api()  
        elif 'SMIQ03B' in self.idn:
            _debug('signal_generator_api.__init__() I choose you simq03b')
            self._api = simq03b_api()
            
        else:
            print("Unknown Signal Generator: "+str(self.idn))
            self._api = sma100b_api() # Just use SMA100B as the default

        # Make sure the class has everything it needs.
        self._api.instrument       = self.instrument
        self._api.idn              = self.idn
        self._api.resource_manager = self.resource_manager
        self._api._write_sleep     = self._write_sleep


    def reset(self):
        """
        Resets the device to factory defaults (RF off).
        """
        return self._api.reset()
    
    def send_list(self, frequencies=[1e9,2e9,3e9,4e9], powers=[-10,-5,-2,0], dwell=0, delay=0):
        """
        Sends the specified list values.
        
        Parameters
        ----------
        frequencies=[1e9,2e9,3e9,4e9]
            List of frequency values (Hz) to touch.
        
        powers=[0,0,0,0]
            List of power values (dBm) to touch.
        
        dwell=0
            In immediate mode for the list sweep, this is how long the generator
            will dwell on a given step.
        
        delay=0
            How long to delay after triggering the next step.
        """
        return self._api.send_list(frequencies, powers, dwell, delay)

    def set_mode(self, mode='List'):
        """
        Sets the generator to be in list or fixed mode.
        
        Paramters
        ---------
        mode='List'
            Set to 'Fixed' for fixed mode.
        """
        return self._api.set_mode(mode)
    
    def get_mode(self):
        """
        Returns 'Fixed' or 'List' depending on the device mode.
        """
        return self._api.get_mode()
    
    def set_list_index(self, n=0):
        """
        Sets the list index, changing the appropriate frequency and power on the 
        output.
        
        Parameters
        ----------
        n=0
            0-referenced index.
        """
        return self._api.set_list_index(n)
        
    def get_list_index(self):
        """
        Gets the current list index.
        """
        return self._api.get_list_index()
    
    def set_output(self, on=False):
        """
        Turns the output on or off.
        """
        return self._api.set_output(on)

    def get_output(self):
        """
        Returns 0 or 1 based on the RF output state.
        """
        return self._api.get_output()

    def set_frequency(self, f=1e9):
        """
        Sets the frequency to f (Hz).
        
        Parameters
        ----------
        f=1e9
            Frequency (Hz)
        """
        return self._api.set_frequency(f)
        
    def get_frequency(self):
        """ 
        Returns the current frequency (Hz).
        """
        return self._api.get_frequency()
    
    def set_power(self, dbm=-30):
        """
        Sets the output power to the specified value (dBm).
        """
        return self._api.set_power(dbm)
    
    def get_power(self):
        """
        Returns the current power level (dBm).
        """
        return self._api.get_power()
    
    def get_list_powers(self):
        """
        Gets the list of powers.
        """
        return self._api.get_list_powers()
        
    def get_list_frequencies(self):
        """
        Gets the list of frequencies. In Hz !
        """
        return self._api.get_list_frequencies()
        
    def get_list_length(self):
        """
        Returns the size of the list sweep.
        """
        return self._api.get_list_length()

    def prepare_for_ESR(self):
        """
        Prepare the instrument for ESR measurement.
        Set the trigger to be external, pulse modulation, etc. 
        """    
        return self._api.prepare_for_ESR()

    def prepare_for_Rabi(self):
        """
        Prepare the signal generator for Rabi:
            Put in fixed mode, modulate the frequency, etc. 
        """
        return self._api.prepare_for_Rabi()
    

class sma100b_api(_mp.visa_tools.visa_api_base):    
    """
    API for SMA100B. This object just defines the functions to be used by the
    base class signal_generator_api.
    """
    def __init__(self): return
        
    def reset(self):
        """
        Resets the device to factory defaults (RF off).
        """
        _debug('api.reset()')
        self.write('*RST')
        self.query('*IDN?') # Pauses operation until fully reset?
    
    def send_list(self, frequencies=[1e9,2e9,3e9,4e9], powers=[-10,-5,-2,0], dwell=1000, delay=0):
        """
        Sends the specified list values.
        
        Parameters
        ----------
        frequencies=[1e9,2e9,3e9,4e9]
            List of frequency values (Hz) to touch.
        
        powers=[0,0,0,0]
            List of power values (dBm) to touch.
        
        dwell=0
            In immediate mode for the list sweep, this is how long the generator
            will dwell on a given step.
        
        delay=0
            How long to delay after triggering the next step.
        """
        _debug('api.send_list()')
        
        # Handle integers or lists for either frequencies or powers
        if not _s.fun.is_iterable(frequencies): frequencies = [frequencies]
        if not _s.fun.is_iterable(powers):      powers      = [powers]
        
        # Handle numpy arrays
        if not type(frequencies) == 'list': frequencies = list(frequencies)
        if not type(powers)      == 'list': powers      = list(powers)
        
        # Handle length-1 arrays:
        if len(frequencies) == 1: frequencies = frequencies*len(powers)
        if len(powers)      == 1: powers      = powers     *len(frequencies)
        
        # Poop if the lengths don't match
        if not len(frequencies) == len(powers): 
            print("ERROR: Lengths must match!")
            return
        
        #The mode switch to Fixed  when we write a power and dwell list. 
        #So I track the initial mode to put it back at the end. 
        initial_mode = self.get_mode()
        
        #First choose a list, otherwise SMA100B is mad
        #To know the available list, the query is 'SOUR1:LIST:CAT?'
        self.write('SOUR1:LIST:SEL "/var/user/list1.lsw"') 
         
        #Prepare the strings for the list command
        str_freq = 'SOUR1:LIST:FREQ ' + str(frequencies[0]) #String for the frequency list command
        str_pow = 'SOUR1:LIST:POW ' + str(powers[0]) #String for the power list command
        str_dwell = 'SOUR1:LIST:DWEL:LIST '+str(dwell) #String for the dwell list command
        for i in range(1,len(frequencies)):
            str_freq += ', ' + str(frequencies[i])
            str_pow += ', ' + str(powers[i])
            str_dwell += ', '+str(dwell)
        
        self.write(str_freq)
        self.write(str_pow)
        self.write(str_dwell)
        
        #Apparently the SMA change to Fixed mode after the power and the Dwell list is send... 
        #So I just switch back to the initial mode to make sure we end up in the same state. 
        self.set_mode(initial_mode)


    def set_mode(self, mode='List'):
        """
        Sets the generator to be in list or fixed mode.
        
        Paramters
        ---------
        mode='List'
            Set to 'Fixed' for fixed mode.
        """
    
        #If we choose list mode    
        if mode.lower() == 'list':
            #First choose a list if there was no, otherwise SMA100B is mad
            #To know the available list, the query is 'SOUR1:LIST:CAT?'
            self.write('SOUR1:LIST:SEL "/var/user/list1.lsw"') 
            
            self.write('OUTP1:STAT ON') #Somehow the SMA100B wants the RF to be ON for switching into list mode.
            self.write('SOUR1:LIST:MODE STEP') #Make Step mode in order to not automatically sweep all the frequencies
            self.write('SOURce1:FREQuency:MODE LIST')
        else:
            #CW and FIXed are synonyms for SMA100B
            self.write('SOURce1:FREQuency:MODE CW')
    
    def get_mode(self):
        """
        Returns 'Fixed' or 'List' depending on the device mode.
        """
        s = self.query('FREQ:MODE?')
        if s == None: return None
        
        s = s.strip()
        if   s == 'CW':  return 'Fixed'
        elif s == 'LIST': return 'List'
        else:
            print('ERROR: Unknown mode '+str(s))
            return
    
    def set_list_index(self, n=0):
        """
        Sets the list index, changing the appropriate frequency and power on the 
        output.
        
        Parameters
        ----------
        n=0
            0-referenced index.
        """
        #We have to be in step mode for being able to set the list index
        self.write('SOUR1:LIST:MODE STEP') #Have to be in STEP mode in order to select the index
        self.write('SOUR1:LIST:IND '+ str(int(n)) ) 
    
    def get_list_index(self):
        """
        Gets the current list index.
        """
        s = self.query('LIST:IND?')
        return int(s)
    
    def set_output(self, on=False):
        """
        Turns the output on or off.
        """
        #Note that, for SMA, switiching off the output set the automatically the mode to Fixed.... !!
        if on: self.write("OUTP1:STAT ON")
        else:  self.write("OUTP1:STAT OFF")
        

    def get_output(self):
        """
        Returns 0 or 1 based on the RF output state.
        """
        x = self.query('OUTP1:STAT?')
        if x == None: return None
        return int(x)

    def set_frequency(self, f=1e9):
        """
        Sets the frequency to f (Hz).
        
        Parameters
        ----------
        f=1e9
            Frequency (Hz)
        """
        self.write('SOUR:FREQ:CW '+str(f))
        
    def get_frequency(self):
        """ 
        Returns the current frequency (Hz).
        """
        x = self.query('SOUR:FREQ:CW?')
        if x == None: return None
        return float(x)
    
    def set_power(self, dbm=-30):
        """
        Sets the output power to the specified value (dBm).
        """
        self.write("SOURce1:POWer:POWer "+str(dbm))
    
    def get_power(self):
        """
        Returns the current power level (dBm).
        """
        x = self.query('SOURce1:POWer:POWer?')
        if x == None: return None
        return float(x)
    
    def get_list_powers(self):
        """
        Gets the list of powers.
        """
        s = self.query('SOUR1:LIST:POW?')
        if s == None: return None
        a = []
        n = 0
        for x in s.split(','):
            try:
                a.append(float(x.strip()))
            except:
                print('ERROR get_list_powers(): non-float in list ', n, x)
            n += 1
        return a
        
    def get_list_frequencies(self):
        """
        Gets the list of frequencies.
        """
        s = self.query('SOUR1:LIST:FREQ?')
        if s == None: return None
        a = []
        n = 0
        for x in s.split(','):
            try:
                a.append(float(x.strip()))
            except:
                print('ERROR get_list_frequencies(): non-float in list ', n, x)
            n += 1
        return a
        
    def get_list_length(self):
        """
        Returns the size of the list sweep.
        """
        s = self.query('SOUR1:LIST:FREQ:POIN?')
        if s == None: return None
        return int(s)


    def prepare_for_ESR(self):
        """
        Prepare the instrument for ESR measurement.
        Set the trigger to be external, pulse modulation, etc. 
        
        Similar to what is doen in the Labview vi "Host SMIQ Command.vi" 
        """
        _debug('sma100b_api: prepare ESR')
        
        # Copy-paste the commands in Labview vi "Host SMIQ Command.vi"
        #This tell to take the pulse External for modulating the output. 
        self.write('SOURce:PULM:SOURce EXT') 
        self.write('SOURce:PULM:STATe ON')
        # Ouput on
        self.write('OUTP ON') 
        # This prepares for a list mode with an external trigger
        self.write('LIST:LEAR')
        self.write('FREQ:MODE LIST')
        self.write('LIST:MODE STEP')
        self.write('TRIG:LIST:SOUR EXT')
        self.write('SOUR:LIST:IND:START 0')
        self.write('SOUR:LIST:IND:STOP   ')     
        # Very important: we unable the display for avoiding glitches
        self.write('SYSTem:DISPlay:UPDate OFF')
        # Other things
        self.write('ABOR')
        self.write('*RST')
        self.write('LIST:SEL "New_list"')
        
    def prepare_for_Rabi(self):
        """
        Prepare the signal generator for Rabi:
            Put in fixed mode, modulate the frequency, etc. 
            
        Similar to what is doen in the Labview vi "Host SMIQ Command.vi" 
        """
        _debug('sma100b_api: prepare for Rabi')
        #This tell to take the pulse External for modulating the output. 
        self.write('SOURce:PULM:SOURce EXT') 
        self.write('SOURce:PULM:STATe ON')     
        # This is also done in Labviw
        self.write('LIST:MODE OFF')
        self.write('ABOR')
        self.write('*RST')
    

class smb100a_api(_mp.visa_tools.visa_api_base):    
    """
    API for SMB100A. This object just defines the functions to be used by the
    base class signal_generator_api.
    """
    def __init__(self): return
        
    def reset(self):
        """
        Resets the device to factory defaults (RF off).
        """
        _debug('api.reset()')
        self.write('*RST')
        self.query('*IDN?') # Pauses operation until fully reset?
    
    def send_list(self, frequencies=[1e9,2e9,3e9,4e9], powers=[-10,-5,-2,0], dwell=1000, delay=0):
        """
        Sends the specified list values.
        
        Parameters
        ----------
        frequencies=[1e9,2e9,3e9,4e9]
            List of frequency values (Hz) to touch.
        
        powers=[0,0,0,0]
            List of power values (dBm) to touch.
        
        dwell=0
            In immediate mode for the list sweep, this is how long the generator
            will dwell on a given step.
        
        delay=0
            How long to delay after triggering the next step.
        """
        _debug('api.send_list()')
        
        # Handle integers or lists for either frequencies or powers
        if not _s.fun.is_iterable(frequencies): frequencies = [frequencies]
        if not _s.fun.is_iterable(powers):      powers      = [powers]
        
        # Handle numpy arrays
        if not type(frequencies) == 'list': frequencies = list(frequencies)
        if not type(powers)      == 'list': powers      = list(powers)
        
        # Handle length-1 arrays:
        if len(frequencies) == 1: frequencies = frequencies*len(powers)
        if len(powers)      == 1: powers      = powers     *len(frequencies)
        
        # Poop if the lengths don't match
        if not len(frequencies) == len(powers): 
            print("ERROR: Lengths must match!")
            return
        
        #The mode switch to Fixed  when we write a power and dwell list. 
        #So I track the initial mode to put it back at the end. 
        initial_mode = self.get_mode()
        
        #First choose a list, otherwise SMA100B is mad
        #To know the available list, the query is 'SOUR1:LIST:CAT?'
        self.write('SOUR1:LIST:SEL "/var/user/list1.lsw"') 
         
        #Prepare the strings for the list command
        str_freq = 'SOUR1:LIST:FREQ ' + str(frequencies[0]) #String for the frequency list command
        str_pow = 'SOUR1:LIST:POW ' + str(powers[0]) #String for the power list command
        str_dwell = 'SOUR1:LIST:DWEL:LIST '+str(dwell) #String for the dwell list command
        for i in range(1,len(frequencies)):
            str_freq += ', ' + str(frequencies[i])
            str_pow += ', ' + str(powers[i])
            str_dwell += ', '+str(dwell)
        
        self.write(str_freq)
        self.write(str_pow)
        self.write(str_dwell)
        
        #Apparently the SMA change to Fixed mode after the power and the Dwell list is send... 
        #So I just switch back to the initial mode to make sure we end up in the same state. 
        self.set_mode(initial_mode)


    def set_mode(self, mode='List'):
        """
        Sets the generator to be in list or fixed mode.
        
        Paramters
        ---------
        mode='List'
            Set to 'Fixed' for fixed mode.
        """
    
        #If we choose list mode    
        if mode.lower() == 'list':
            #First choose a list if there was no, otherwise SMA100B is mad
            #To know the available list, the query is 'SOUR1:LIST:CAT?'
            self.write('SOUR1:LIST:SEL "/var/user/list1.lsw"') 
            
            self.write('OUTP1:STAT ON') #Somehow the SMA100B wants the RF to be ON for switching into list mode.
            self.write('SOUR1:LIST:MODE STEP') #Make Step mode in order to not automatically sweep all the frequencies
            self.write('SOURce1:FREQuency:MODE LIST')
        else:
            #CW and FIXed are synonyms for SMA100B
            self.write('SOURce1:FREQuency:MODE CW')
    
    def get_mode(self):
        """
        Returns 'Fixed' or 'List' depending on the device mode.
        """
        s = self.query('FREQ:MODE?')
        if s == None: return None
        
        s = s.strip()
        if   s == 'CW':  return 'Fixed'
        elif s == 'LIST': return 'List'
        else:
            print('ERROR: Unknown mode '+str(s))
            return
    
    def set_list_index(self, n=0):
        """
        Sets the list index, changing the appropriate frequency and power on the 
        output.
        
        Parameters
        ----------
        n=0
            0-referenced index.
        """
        #We have to be in step mode for being able to set the list index
        self.write('SOUR1:LIST:MODE STEP') #Have to be in STEP mode in order to select the index
        self.write('SOUR1:LIST:IND '+ str(int(n)) ) 
    
    def get_list_index(self):
        """
        Gets the current list index.
        """
        s = self.query('LIST:IND?')
        return int(s)
    
    def set_output(self, on=False):
        """
        Turns the output on or off.
        """
        #Note that, for SMA, switiching off the output set the automatically the mode to Fixed.... !!
        if on: self.write("OUTP1:STAT ON")
        else:  self.write("OUTP1:STAT OFF")
        

    def get_output(self):
        """
        Returns 0 or 1 based on the RF output state.
        """
        x = self.query('OUTP1:STAT?')
        if x == None: return None
        return int(x)

    def set_frequency(self, f=1e9):
        """
        Sets the frequency to f (Hz).
        
        Parameters
        ----------
        f=1e9
            Frequency (Hz)
        """
        self.write('SOUR:FREQ:CW '+str(f))
        
    def get_frequency(self):
        """ 
        Returns the current frequency (Hz).
        """
        x = self.query('SOUR:FREQ:CW?')
        if x == None: return None
        return float(x)
    
    def set_power(self, dbm=-30):
        """
        Sets the output power to the specified value (dBm).
        """
        self.write("SOURce1:POWer:POWer "+str(dbm))
    
    def get_power(self):
        """
        Returns the current power level (dBm).
        """
        x = self.query('SOURce1:POWer:POWer?')
        if x == None: return None
        return float(x)
    
    def get_list_powers(self):
        """
        Gets the list of powers.
        """
        s = self.query('SOUR1:LIST:POW?')
        if s == None: return None
        a = []
        n = 0
        for x in s.split(','):
            try:
                a.append(float(x.strip()))
            except:
                print('ERROR get_list_powers(): non-float in list ', n, x)
            n += 1
        return a
        
    def get_list_frequencies(self):
        """
        Gets the list of frequencies.
        """
        s = self.query('SOUR1:LIST:FREQ?')
        if s == None: return None
        a = []
        n = 0
        for x in s.split(','):
            try:
                a.append(float(x.strip()))
            except:
                print('ERROR get_list_frequencies(): non-float in list ', n, x)
            n += 1
        return a
        
    def get_list_length(self):
        """
        Returns the size of the list sweep.
        """
        s = self.query('SOUR1:LIST:FREQ:POIN?')
        if s == None: return None
        return int(s)

    def prepare_for_ESR(self):
        """
        Prepare the instrument for ESR measurement.
        Set the trigger to be external, pulse modulation, etc. 
        
        Similar to what is doen in the Labview vi "Host SMIQ Command.vi" 
        """
        _debug('smb100a_api: prepare ESR')
        
        # Copy-paste the commands in Labview vi "Host SMIQ Command.vi"

        # Very important: we unable the display for avoiding glitches
        self.write('SYSTem:DISPlay:UPDate OFF')
        # Other things
        self.write('ABOR')
        self.write('*RST')
        self.write('LIST:SEL "New_list"')
        
        
        # This prepares for a list mode with an external trigger
        self.write('LIST:LEAR')
        self.write('FREQ:MODE LIST')
        self.write('LIST:MODE STEP')
        self.write('TRIG:LIST:SOUR EXT')
        self.write('SOUR:LIST:IND:START 0')
        # Like Labview, set the stop index
        N = self.get_list_length()
        self.write('SOUR:LIST:IND:STOP %d'%(N-1))     


        
        #This tell to take the pulse External for modulating the output. 
        self.write('SOURce:PULM:SOURce EXT') 
        self.write('SOURce:PULM:STATe ON')
        # Ouput on
        self.write('OUTP ON') 
        
    def prepare_for_Rabi(self):
        """
        Prepare the signal generator for Rabi:
            Put in fixed mode, modulate the frequency, etc. 
            
        Similar to what is doen in the Labview vi "Host SMIQ Command.vi" 
        """
        _debug('smb100a_api: prepare for Rabi')
 
        # This is also done in Labviw
        self.write('LIST:MODE OFF')
        self.write('ABOR')
        self.write('*RST')
        # Same command as Labview
        self.write('OUTP:STAT ON')
        self.write('SOUR:FREQ:MODE CW')
        #This tell to take the pulse External for modulating the output. 
        self.write('SOURce:PULM:SOURce EXT') 
        self.write('SOURce:PULM:STATe ON')
        
        
    
class anapico_api(_mp.visa_tools.visa_api_base):
    """
    API for Anapico. This object just defines the functions to be used by the
    base class signal_generator_api.
    """
    def __init__(self): return
        
    def reset(self):
        """
        Resets the device to factory defaults (RF off).
        """
        _debug('api.reset()')
        self.write('*RST')
        self.query('*IDN?') # Pauses operation until fully reset?
    
    def send_list(self, frequencies=[1e9,2e9,3e9,4e9], powers=[-10,-5,-2,0], dwell=0, delay=0):
        """
        Sends the specified list values.
        
        Parameters
        ----------
        frequencies=[1e9,2e9,3e9,4e9]
            List of frequency values (Hz) to touch.
        
        powers=[0,0,0,0]
            List of power values (dBm) to touch.
        
        dwell=0
            In immediate mode for the list sweep, this is how long the generator
            will dwell on a given step.
        
        delay=0
            How long to delay after triggering the next step.
        """
        _debug('api.send_list()')
        
        # Handle integers or lists for either frequencies or powers
        if not _s.fun.is_iterable(frequencies): frequencies = [frequencies]
        if not _s.fun.is_iterable(powers):      powers      = [powers]
        
        # Handle numpy arrays
        if not type(frequencies) == 'list': frequencies = list(frequencies)
        if not type(powers)      == 'list': powers      = list(powers)
        
        # Handle length-1 arrays:
        if len(frequencies) == 1: frequencies = frequencies*len(powers)
        if len(powers)      == 1: powers      = powers     *len(frequencies)
        
        # Poop if the lengths don't match
        if not len(frequencies) == len(powers): 
            print("ERROR: Lengths must match!")
            return
        
        # The anapico, annoyingly, will only send a list if it's not in list mode
        original_mode = self.get_mode()
        if original_mode=='List': self.set_mode('Fixed')
        
        # Assemble the long-ass command
        command = "LIST:POW "        
        for p in powers: command += str(p)+","
        self.write(command)
      
        # Do the same for the frequencies
        command = "LIST:FREQ "
        for f in frequencies: command += str(f)+","          
        self.write(command)
            
        # Set dwell and delay
        self.write("LIST:DWEL " + str(dwell))
        self.write("LIST:DEL " + str(delay))
        
        # Set it back if we're supposed to
        if original_mode == 'List': self.set_mode('List')

    def set_mode(self, mode='List'):
        """
        Sets the generator to be in list or fixed mode.
        
        Paramters
        ---------
        mode='List'
            Set to 'Fixed' for fixed mode.
        """
        
        if mode.lower() == 'list':
            
            # Set sweep to manual mode    
            self.write("FREQ:MODE LIST")
            self.write("POW:MODE LIST")
            self.write("LIST:MODE MAN")

        # Fixed Mode
        else:
            # Set power and frequency to either fixed or list mode
            self.write("FREQ:MODE FIX")
            self.write("POW:MODE FIX")
            
        # Hack
        # Try to interrupt
        print('Bug workaround (long wait!)...')
        
        # Wait until it works
        failed = True
        n      = 0
        while failed:
            _t.sleep(0.25)
            try:   
                print('   TIMER-OUTER', self.query('*IDN?'))
                failed = False
            except: 
                n += 1
                print('Bug workaround: time out #'+str(n))
        print('Bug workaround: all done!')
    
    def get_mode(self):
        """
        Returns 'Fixed' or 'List' depending on the device mode.
        """
        s = self.query('FREQ:MODE?')
        if s == None: return None
        
        s = s.strip()
        if   s == 'FIX':  return 'Fixed'
        elif s == 'LIST': return 'List'
        else:
            print('ERROR: Unknown mode '+str(s))
            return
    
    def set_list_index(self, n=0):
        """
        Sets the list index, changing the appropriate frequency and power on the 
        output.
        
        Parameters
        ----------
        n=0
            0-referenced index.
        """
        self.write("LIST:MAN " + str(int(n+1)))
    
    def get_list_index(self):
        """
        Gets the current list index.
        """
        s = self.query('LIST:MAN?')
        if s == None: return None
        return int(s)-1
    
    def set_output(self, on=False):
        """
        Turns the output on or off.
        """
        if on: self.write("OUTP ON")
        else:  self.write("OUTP OFF")

    def get_output(self):
        """
        Returns 0 or 1 based on the RF output state.
        """
        x = self.query('OUTP?')
        if x == None: return None
        return int(x)

    def set_frequency(self, f=1e9):
        """
        Sets the frequency to f (Hz).
        
        Parameters
        ----------
        f=1e9
            Frequency (Hz)
        """
        self.write('FREQ '+str(f))
        
    def get_frequency(self):
        """ 
        Returns the current frequency (Hz).
        """
        x = self.query('FREQ?')
        if x == None: return None
        return float(x)
    
    def set_power(self, dbm=-30):
        """
        Sets the output power to the specified value (dBm).
        """
        self.write("POW "+str(dbm))
    
    def get_power(self):
        """
        Returns the current power level (dBm).
        """
        x = self.query('POW?')
        if x == None: return None
        return float(x)
    
    def get_list_powers(self):
        """
        Gets the list of powers.
        """
        s = self.query('LIST:POW?')
        if s == None: return None
        a = []
        n = 0
        for x in s.split(','):
            try:
                a.append(float(x.strip()))
            except:
                print('ERROR get_list_powers(): non-float in list ', n, x)
            n += 1
        return a
        
    def get_list_frequencies(self):
        """
        Gets the list of frequencies.
        """
        s = self.query('LIST:FREQ?')
        if s == None: return None
        a = []
        n = 0
        for x in s.split(','):
            try:
                a.append(float(x.strip()))
            except:
                print('ERROR get_list_frequencies(): non-float in list ', n, x)
            n += 1
        return a
        
    def get_list_length(self):
        """
        Returns the size of the list sweep.
        """
        s = self.query('LIST:FREQ:POIN?')
        if s == None: return None
        return int(s)
    
    def prepare_for_ESR(self):
        """
        Prepare the instrument for ESR measurement.
        Set the trigger to be external, pulse modulation, etc. 
        """
        _debug('Anapico: prepare ESR')
        # This is all for the ANAPICO to use the external trigger. 
        # BONUS for preparing the list with the external trigger. 
        _debug('Testing query: ', self.query('*IDN?'))
        _debug('Source for Trigger?: ', self.query('TRIG:SEQ:SOUR?'))
        self.write('TRIG:SEQ:SOUR EXT') # Set the external trigger to ext
        _debug('Source for Trigger?: ', self.query('TRIG:SEQ:SOUR?'))
        _debug('First frequency?: ', self.query('SOUR:FREQ:STAR?'))
        _debug('Last  frequency?: ', self.query('SOUR:FREQ:STOP?'))
        
        # Prepare the list mode
        self.write('SOUR:FREQ:MODE LIST') # Set the frequency mode to list
        _debug('Frequency mode ?: ', self.query('SOUR:FREQ:MODE?'))
        self.write('SOUR:POW:MODE LIST') # Set the power mode to list
        _debug('Power mode ?: ', self.query('SOUR:POW:MODE?'))
        self.write('SOUR:LIST:MODE AUTO') # Set the list mode to auto
        _debug('List mode ?: ', self.query('SOUR:LIST:MODE?'))
#        self.api.write('TRIG:SEQ:TYPE GATE') # An external trigger signal repeatedly starts and stops the waveform’s playback.
        self.write('TRIG:SEQ:TYPE POIN')# Upon triggering, only a single point of the sweep (list) is played.
        _debug('Trig type?: ', self.query('TRIG:SEQ:TYPE?'))
        
        # Set stuff for the modulation
        self.write('SOUR:PULM:SOUR EXT')# Set the pulse modulation to be external
        _debug('Pulse modulation source?: ', self.query('SOUR:PULM:SOUR?'))
        self.write('SOUR:PULM:STAT ON') # Switch the pulse modulation ON
        _debug('State of pulse modulation? ', self.query('SOUR:PULM:STAT?'))
        self.write('SOUR:PULM:POL NORM') # Polarity NORMal, in case it was INVerted
        _debug('Polarity of modulation?: ', self.query('SOUR:PULM:POL?'))        

        
    def prepare_for_Rabi(self):
        """
        Prepare the signal generator for Rabi:
            Put in fixed mode, modulate the frequency, etc. 
        """
        _debug('Anapico: prepare for Rabi')

        self.write('SOUR:FREQ:MODE FIX') # Set the frequency mode to Fix
        print('Frequency mode ?: ', self.query('SOUR:FREQ:MODE?'))

        # Set stuff for the modulation
        self.write('SOUR:PULM:SOUR EXT')# Set the pulse modulation to be external
        print('Pulse modulation source?: ', self.query('SOUR:PULM:SOUR?'))
        self.write('SOUR:PULM:STAT ON') # Switch the pulse modulation ON
        print('State of pulse modulation? ', self.query('SOUR:PULM:STAT?'))
        self.write('SOUR:PULM:POL NORM') # Polarity NORMal, in case it was INVerted
        print('Polarity of modulation?: ', self.query('SOUR:PULM:POL?'))             
        
        
        

class simq03b_api(_mp.visa_tools.visa_api_base):    
    """
    API for SMIQ03B. This object just defines the functions to be used by the
    base class signal_generator_api.
    """
    def __init__(self): return
        
    def reset(self):
        """
        Resets the device to factory defaults (RF off).
        """
        _debug('simq03b_api.reset')
        self.write('*RST')
        self.query('*IDN?') # Pauses operation until fully reset?
    
    def send_list(self, frequencies=[1e9,2e9,3e9,4e9], powers=[-10,-5,-2,0], dwell=0.01, delay=0):
        """
        Sends the specified list values.
        
        Parameters
        ----------
        frequencies=[1e9,2e9,3e9,4e9]
            List of frequency values (Hz) to touch.
        
        powers=[0,0,0,0]
            List of power values (dBm) to touch.
        
        dwell=0 
            (IN second!) In immediate mode for the list sweep, this is how long the generator
            will dwell on a given step.
        
        delay=0
            How long to delay after triggering the next step.
        """
        _debug('simq03b_api.send_list')
        
        # Handle integers or lists for either frequencies or powers
        if not _s.fun.is_iterable(frequencies): frequencies = [frequencies]
        if not _s.fun.is_iterable(powers):      powers      = [powers]
        
        # Handle numpy arrays
        if not type(frequencies) == list: frequencies = list(frequencies)
        if not type(powers)      == list: powers      = list(powers)
        
        # Handle length-1 arrays:
        if len(frequencies) == 1: frequencies = frequencies*len(powers)
        if len(powers)      == 1: powers      = powers     *len(frequencies)
        
        # Poop if the lengths don't match
        if not len(frequencies) == len(powers): 
            print("ERROR: Lengths must match!")
            return
        
        #The mode switch to Fixed  when we write a power and dwell list. 
        #So I track the initial mode to put it back at the end. 
        initial_mode = self.get_mode()
        
        # Let's choose a list. 
        #To know the available list, the query is 'SOUR1:LIST:CAT?'
        self.write('SOUR:LIST:SEL /VAR/USE') 
         
        #Prepare the strings for the list command
        str_freq = 'SOUR:LIST:FREQ ' + str(frequencies[0]) #String for the frequency list command
        str_pow   = 'SOUR:LIST:POW ' + str(powers[0]) #String for the power list command
        str_dwell = 'SOUR:LIST:DWEL '+str(dwell) #String for the dwell list command
        for i in range(1,len(frequencies)):
            str_freq += ', ' + str(frequencies[i])
            str_pow += ', ' + str(powers[i])
        
        # For debugging
        print(str_freq)
        print(str_pow)
        print(str_dwell)
        
        self.write(str_freq)
        self.write(str_pow)
        self.write(str_dwell)
        
        # In SMIQ manual, it says:
        # Caution: This command has to be given after every creating and changing of a list.
        self.write('SOUR:LIST:LEARn')
        
        #Apparently the SMA change to Fixed mode after the power and the Dwell list is send... 
        #So I just switch back to the initial mode to make sure we end up in the same state. 
        self.set_mode(initial_mode)


    def set_mode(self, mode='List'):
        """
        Sets the generator to be in list or fixed mode.
        
        Paramters
        ---------
        mode='List'
            Set to 'Fixed' for fixed mode.
        """
        _debug('simq03b_api.set_mode')
        
        #If we choose list mode    
        if mode.lower() == 'list':
            #First choose a list if there was no, otherwise SMA100B is mad
            #To know the available list, the query is 'SOUR1:LIST:CAT?'
            self.write('SOUR1:LIST:SEL "/var/user/list1.lsw"') 
            
            self.write('OUTP1:STAT ON') #Somehow the SMA100B wants the RF to be ON for switching into list mode.
            self.write('SOUR1:LIST:MODE STEP') #Make Step mode in order to not automatically sweep all the frequencies
            self.write('SOURce:FREQuency:MODE LIST')
        else:
            #CW and FIXed are synonyms for SMA100B
            self.write('SOURce:FREQuency:MODE CW')
    
    def get_mode(self):
        """
        Returns 'Fixed' or 'List' depending on the device mode.
        """
        _debug('simq03b_api.get_mode')
        
        s = self.query('FREQ:MODE?')
        if s == None: return None
        
        s = s.strip()
        if   s == 'CW':  return 'Fixed'
        elif s == 'LIST': return 'List'
        else:
            print('ERROR: Unknown mode '+str(s))
            return
    
    def set_list_index(self, n=0):
        """
        Sets the list index, changing the appropriate frequency and power on the 
        output.
        
        Parameters
        ----------
        n=0
            0-referenced index.
        """
        _debug('simq03b_api.set_list_index')
        #We have to be in step mode for being able to set the list index
        self.write('SOUR1:LIST:MODE STEP') #Have to be in STEP mode in order to select the index
        self.write('SOUR1:LIST:IND '+ str(int(n)) ) 
    
    def get_list_index(self):
        """
        Gets the current list index.
        """
        _debug('simq03b_api.get_list_index')
        
        s = self.query('LIST:IND?')
        return int(s)
    
    def set_output(self, on=False):
        """
        Turns the output on or off.
        """
        _debug('simq03b_api.set_output')
        
        #Note that, for SMA, switiching off the output set the automatically the mode to Fixed.... !!
        if on: self.write("OUTP:STAT ON")
        else:  self.write("OUTP:STAT OFF")
        

    def get_output(self):
        """
        Returns 0 or 1 based on the RF output state.
        """
        _debug('simq03b_api.get_output')
        
        x = self.query('OUTP:STAT?')
        if x == None: return None
        print('Result is ', x) # For knowing the bug that we something have
        return int(x)

    def set_frequency(self, f=1e9):
        """
        Sets the frequency to f (Hz).
        
        Parameters
        ----------
        f=1e9
            Frequency (Hz)
        """
        _debug('simq03b_api.set_frequency')
        
        self.write('SOUR:FREQ:CW '+str(f))
        
    def get_frequency(self):
        """ 
        Returns the current frequency (Hz).
        """
        _debug('simq03b_api.get_frequency')
        
        x = self.query('SOUR:FREQ:CW?')
        if x == None: return None
        return float(x)
    
    def set_power(self, dbm=-30):
        """
        Sets the output power to the specified value (dBm).
        """
        _debug('simq03b_api.set_power')
        
        self.write("POWer "+str(dbm))
    
    def get_power(self):
        """
        Returns the current power level (dBm).
        """
        _debug('simq03b_api.get_power')
        
        x = self.query('POWer?')
        if x == None: return None
        return float(x)
    
    def get_list_powers(self):
        """
        Gets the list of powers.
        """
        _debug('simq03b_api.get_list_powers')
        
        s = self.query('SOUR:LIST:POW?')
        if s == None: return None
        a = []
        n = 0
        for x in s.split(','):
            try:
                a.append(float(x.strip()))
            except:
                print('ERROR get_list_powers(): non-float in list ', n, x)
            n += 1
        return a
        
    def get_list_frequencies(self):
        """
        Gets the list of frequencies.
        """
        _debug('simq03b_api.get_list_frequencies')
        
        s = self.query('SOUR:LIST:FREQ?')
        if s == None: return None
        a = []
        n = 0
        for x in s.split(','):
            try:
                a.append(float(x.strip()))
            except:
                print('ERROR get_list_frequencies(): non-float in list ', n, x)
            n += 1
        return a
        
    def get_list_length(self):
        """
        Returns the size of the list sweep.
        """
        _debug('simq03b_api.get_list_length')
        
        s = self.query('SOUR1:LIST:FREQ:POIN?')
        if s == None: return None
        return int(s)


    def prepare_for_ESR(self):
        """
        Prepare the instrument for ESR measurement.
        Set the trigger to be external, pulse modulation, etc. 
        """
        _debug('simq03b_api: prepare ESR')
        # Not directly used yet
        
    def prepare_for_Rabi(self):
        """
        Prepare the signal generator for Rabi:
            Put in fixed mode, modulate the frequency, etc. 
        """
        _debug('simq03b_api: prepare for Rabi')
        # Not directly used yet



class fake_api():
    """
    API for Anapico. This object just defines the functions to be used by the
    base class signal_generator_api.
    
    This is a fake API. Meant for testing code without access to an instrument. 
    
    Note: it is not completed yet. 
    """
    def __init__(self):
        
        # Fake attributes
        self.instrument = 'Houla'
        self.close = 'Yo'
        
    def reset(self):
        """
        Resets the device to factory defaults (RF off).
        """
        _debug('api.reset()')
        self.write('*RST')
        self.query('*IDN?') # Pauses operation until fully reset?
    
    def write(self, string='Yo'):
        """
        Fake wrtting function
        """
        return
    def query(self, string='Whats up?'):
        """
        Fake query function
        """
        return 'Knock Knock'
    
        return
        
    
    def send_list(self, frequencies=[1e9,2e9,3e9,4e9], powers=[-10,-5,-2,0], dwell=0, delay=0):
        """
        Sends the specified list values.
        
        Parameters
        ----------
        frequencies=[1e9,2e9,3e9,4e9]
            List of frequency values (Hz) to touch.
        
        powers=[0,0,0,0]
            List of power values (dBm) to touch.
        
        dwell=0
            In immediate mode for the list sweep, this is how long the generator
            will dwell on a given step.
        
        delay=0
            How long to delay after triggering the next step.
        """
        _debug('api.send_list()')
        
        # Handle integers or lists for either frequencies or powers
        if not _s.fun.is_iterable(frequencies): frequencies = [frequencies]
        if not _s.fun.is_iterable(powers):      powers      = [powers]
        
        # Handle numpy arrays
        if not type(frequencies) == 'list': frequencies = list(frequencies)
        if not type(powers)      == 'list': powers      = list(powers)
        
        # Handle length-1 arrays:
        if len(frequencies) == 1: frequencies = frequencies*len(powers)
        if len(powers)      == 1: powers      = powers     *len(frequencies)
        
        # Poop if the lengths don't match
        if not len(frequencies) == len(powers): 
            print("ERROR: Lengths must match!")
            return
        
        # Copy the input
        self.fs = frequencies
        self.ps = powers
        self.dwell = dwell
        self.delay = delay

    def set_mode(self, mode='List'):
        """
        Sets the generator to be in list or fixed mode.
        
        Paramters
        ---------
        mode='List'
            Set to 'Fixed' for fixed mode.
        """
        
        self.mode = mode
    
    def get_mode(self):
        """
        Returns 'Fixed' or 'List' depending on the device mode.
        """
        return self.mode
    
    def set_list_index(self, n=0):
        """
        Sets the list index, changing the appropriate frequency and power on the 
        output.
        
        Parameters
        ----------
        n=0
            0-referenced index.
        """
        self.n = n
    
    def get_list_index(self):
        """
        Gets the current list index.
        """
        return self.n
    
    def set_output(self, on=False):
        """
        Turns the output on or off.
        """
        self.on = on

    def get_output(self):
        """
        Returns 0 or 1 based on the RF output state.
        """
        return self.on

    def set_frequency(self, f=1e9):
        """
        Sets the frequency to f (Hz).
        
        Parameters
        ----------
        f=1e9
            Frequency (Hz)
        """
        self.f = f
        
    def get_frequency(self):
        """ 
        Returns the current frequency (Hz).
        """
        return self.f
    
    def set_power(self, dbm=-30):
        """
        Sets the output power to the specified value (dBm).
        """
        self.p = dbm
    
    def get_power(self):
        """
        Returns the current power level (dBm).
        """
        return self.p
    
    def get_list_powers(self):
        """
        Gets the list of powers.
        """
        return self.ps
        
    def get_list_frequencies(self):
        """
        Gets the list of frequencies.
        """
        return self.fs
        
    def get_list_length(self):
        """
        Returns the size of the list sweep.
        """
        return len(self.ps)


if __name__ == '__main__':
    
    _mp.visa_tools._debug_enabled = True
    _debug_enabled                = True
    
    # Do stud with the API
    











