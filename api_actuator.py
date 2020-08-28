# -*- coding: utf-8 -*-
"""
Created on Mon Jan 20 14:18:37 2020

Goal: Define a class which will allow to talk to the conex. 

I get inspired from the code from Ali.Eftekhari, who worked for NewPort (for the CONEX)

The goal of this script is to be run by its own, without requiring other script 
for the class definition. 

All the command for the conex are found in the user manual called
CONEX-CC controller documenation, chapter 2.0

ATTEMP to use the class CONEX inside the mcphysics GUI. 

@author: Childresslab, Michael
"""



#from CONEX_controller import CONEX 
#import time
import mcphysics   as _mp
import time

import traceback
_p = traceback.print_last #Very usefull command to use for getting the last-not-printed error


# Debug stuff.
_mp.visa_tools._debug_enabled = False
_debug_enabled                = False

def _debug(*a):
    if _debug_enabled: 
        s = []
        for x in a: s.append(str(x))
        print(', '.join(s))


        
class ApiActuator(_mp.visa_tools.visa_api_base):
    """
    General actuator API base. This will connect and then, based on
    the model number, inherit all the commands from one of the specific model
    classes.
    """
    def __init__(self, name='COM4', pyvisa_py=False, simulation=False, timeout=100e3, write_sleep=0.1, **kwargs): 
        """
        Visa-based connection to the Anapico signal generator.
        """
        _debug('ApiActuator.__init__()', pyvisa_py, simulation, timeout, write_sleep)
        
        # Run the core setup.
        _mp.visa_tools.visa_api_base.__init__(self, name, pyvisa_py, simulation, timeout=timeout, write_sleep=write_sleep, **kwargs)
        
        #Inherit the functionality
        self._api = CONEX_api()
        self.apiTest = CONEX_api()
        
        # Make sure the class has everything it needs.
        self._api.instrument       = self.instrument
        self._api.idn              = self.idn
        self._api.resource_manager = self.resource_manager
        self._api._write_sleep     = self._write_sleep
        
        self.apiTest.instrument       = self.instrument
        self.apiTest.idn              = self.idn
        self.apiTest.resource_manager = self.resource_manager
        self.apiTest._write_sleep     = self._write_sleep
        
    def reset(self):
        """
        Reset the actuator
        """
        _debug('ApiActuator.reset()')
        
        return self._api.reset()
        
    def get_state(self):
        """
        Return the state. 
        """
        _debug('ApiActuator.get_state()')
        return self._api.get_state()
    
    def set_position_abs(self, r):
        """
        Move the actuator at a position r (in mm). 
        """
        return self._api.set_position_abs(r)
    
    def get_position(self):
        """
        Get the actuator position (in mm). 
        """
        return self._api.get_position()

    def set_velocity(self, v):
        """
        Set the velocity of the actuator when they move. 
        The unit is "units/sec", according to the literrature... lol
        """
        return self._api.set_velocity(v)
        
        
    
        
    def stop_motion(self):
        """
        Stop the motion ! 
        """
        return self._api.stop_motion()   
        
class CONEX_api(_mp.visa_tools.visa_api_base):
    """
    API for the one CONEX from newport
    This object just defines the functions to be used by an other
    base class. (This base class is not written yet, at the moment I write this).

    """
    
    def __init__(self): 
        """
        COMPort: The COMPort of the actuator used. 
        """
        _debug('CONEX_api._init__()')
        
#        #Connect to the actuator. 
#        self.rm=visa.ResourceManager() #Usefull to acces to the ressource manager. 
#        self.conex=self.rm.open_resource(COMPort, baud_rate=921600, timeout=2000, data_bits=8, write_termination='\r\n')
#        #Verify if it worked
#        print( self.query('1VE')[:-2] ) #check the firmware version
#        
#        #Set the COMPort
#        self.COMPort = COMPort
        return
        
    def reset(self):
        """
        Reset the conex, and put them back in ready state.
        Important: the screw of the actuator will be reset at their minimal lenght before going to the ready state
        There is no much to do with that, because the actuator need to know where is the zero.   
        The HOMING option that we can set with the command 'mmHTnn' does not allow to fix that. 
        """
        _debug('CONEX_api.reset(self)')
        
        self.write('1RS') #Reset, equivalent to a power-up. The state should end up in NOT REFERENCED
        #Delay a little bit before the next command. 
        time.sleep(0.500) #500ms The communication rate is about 50Hz, so 20ms. 
        self.write('1OR') #Go toward  Ready state
        #Warn with a print for now. In the GUI there should be a pop-up window. 
        print('Warning: the screw are resetting !!')      
        
    def get_state(self):
        """
        Return the state
        """
        _debug('CONEX_api.get_state()')
        
        # For knowing the meaning of the returned string, look at p.50 of the 
        # controller documentation. 
        strState = self.query('1TS?)')[7:9] #This extract a number corresponding to the state. 
        if strState == '33':
            return 'READY from MOVING'
        elif strState == '32':
            return 'READY from HOMING'
        elif strState == '28':
            return 'MOVING'
        elif strState == '1E':
            return 'HOMING'
        elif strState == '0A':
            return 'NOT REFERENCED from RESET'
        elif strState == '3C':
            return 'DISABLE from READY.'        
        else:
            return strState #Return the number that we can looking in the manual under the description of the command 'TS'
    
    def get_COMPort(self):
        """
        Return the COMPort string
        """
        return self.COMPort
        
        
    def get_upLimit(self):
        """
        Return the upper limit of the actuator position. 
        """
        strHigh = self.query('1SR?') #Get the string of upper limit
        return float(strHigh[3:]) #Convert into a float 
        
    def get_lowLimit(self):
        """
        Return the lower limit of the actuator position. 
        """
        strHigh = self.query('1SL?') #Get the string of upper limit
        return float(strHigh[3:]) #Convert into a float 
    
    def set_position_abs(self, r):
        """
        Move the actuator at a position r (in mm). 
        
        """
        _debug('CONEX_api.set_position_abs(self, r) r = '+str(r))
        
        #Return and send an error if the position is outside of the limit
        if r > self.get_upLimit():
            print('ERROR: set_posistion_abs() r above the upper limit!')
            return
        if r < self.get_lowLimit():
            print('ERROR: set_posistion_abs() r below the lower limit!')
            return
        #Send the command to move at position r
        self.write('1PA'+str(r))
        
    def get_position(self):
        """
        Get the position of the actuator (in mm)
        """
        _debug('CONEX_api.get_position_abs(self)')

        strPos = self.query('1TP?') #Get the stirng of the position
        return float(strPos[3:]) #Convert into float
        
    def set_velocity(self, v):
        """
        Set the velocity of the actuator when they move. 
        The unit is "units/sec", according to the literrature... lol
        """
        _debug('CONEX_api.set_velocitys(self)')
        #Send the command to set the velovity v
        self.write('1VA' + str(v))
        
        
        
    def stop_motion(self):
        """
        Stop the motion. 
        """
        _debug('CONEX_api.stop_motion(self)')
        self.write('1ST')        



     

        
                    
        
        
    
        



#By default set the object
if __name__ == '__main__':
#    cc = ApiActuator().
    self = actuator(name='CONEX') #This will pop-up the GUI
   
   