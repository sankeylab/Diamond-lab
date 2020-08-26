# -*- coding: utf-8 -*-
"""
Created on Fri Aug 21 10:41:45 2020

@author: Childresslab
"""

from api_actuator import ApiActuator
import spinmob     as _s
from spinmob import egg
import time
import mcphysics   as _mp
import numpy as np

import traceback
_p = traceback.print_last #Very usefull command to use for getting the last-not-printed error

#Debug
_debug_enabled           = False






def _debug(*a):
    if _debug_enabled: 
        s = []
        for x in a: s.append(str(x))
        print(', '.join(s))


class GUISingleActuator(_mp.visa_tools.visa_gui_base):
    """
    Graphical front-end for the actuator.
    
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

    def __init__(self, name='Actuator', show=True, block=False, timeout=2e3, write_sleep=0.1, pyvisa_py=False):
        _debug('GUISingleActuator.__init__()')
        
        # Run the basic stuff.
        _mp.visa_tools.visa_gui_base.__init__(self, name, show, block, ApiActuator, timeout=timeout, write_sleep=write_sleep, pyvisa_py=pyvisa_py, hello_query='1VE?', baud_rate=921600)
    
        #Give a name to the GUI, for helping debugging
        self.name = 'Bibi'
    
        # Add stuff to the GUI.
        #On the top
        self.button_reset       = self.grid_top.add(egg.gui.Button('Reset', checkable=True)).set_width(60).disable()
        self.button_state       = self.grid_top.add(egg.gui.Button('State', checkable=True)).set_width(75).disable()
        self.button_move        = self.grid_top.add(egg.gui.Button('Move', checkable=True)).set_width(100).disable()
        self.button_stop        = self.grid_top.add(egg.gui.Button('STOP', checkable=True, )).set_width(100).enable()
        self.button_stop.set_colors(text='red', background='yellow') #Be fancy
        #Elsewhere
        self.label_position     = self.grid_top.place_object(egg.gui.Label('Position = XX mm'), 0,1,column_span=2)
        self.label_state        = self.grid_top.place_object(egg.gui.Label('State = LOL'), 2,1,column_span=2)  
        self.label_name        = self.grid_top.place_object(egg.gui.Label('Name = '+self.name), 4,1,column_span=1)  
        
        #This is some setting
        self.settings.add_parameter('Motion/Target_position', bounds=(0,25), suffix=' mm')
        self.settings.add_parameter('Motion/Speed'          , bounds=(0,2) , suffix=' units/sec')
        
        
        #Add a timer for some update when the actuator moves
        self.timer_moving = egg.gui.Timer(interval_ms=500, single_shot=False)
        self.timer_moving._widget.timeout.connect( self._update ) #Each time it tick, it gonna do the function self._update
        
        # Place the instrument name at a more convient place
        self.grid_top.place_object(self.label_instrument_name,0,2,column_span=1)
        
        #Connection of the button to the function
        self.button_state           .signal_toggled.connect(self._button_state_toggled)
        self.button_reset           .signal_toggled.connect(self._button_reset_toggled)
        self.button_move            .signal_toggled.connect(self._button_move_toggled)
        self.button_stop            .signal_toggled.connect(self._button_stop_toggled)
        self.button_connect         .signal_toggled.connect(self._update)
        
        #Enable the button, set them weither they are checked or not. 
        self.button_state.set_checked(False,  block_events=True).enable()
        self.button_reset.set_checked(False,  block_events=True).enable()
        self.button_move .set_checked(False,  block_events=True).enable()
           
        
    def set_name(self, name):
        """
        Set the name of the GUI
        """
        self.name = name
        #Update the name in the GUI
        self.label_name.set_text('Name = '+name)
        
    def get_name(self):
        """
        Get the name of the GUI
        """
        return self.name
        
    def _button_reset_toggled(self, *a):
        """
        Reset the actuator. 
        WARNING: this will put back the actuator in position 0. 
        """
        _debug('GUISingleActuator.button_reset_toggled()')
        
        self.timer_moving.start() #It's gonna move, so update
        self.api.reset()
        #Put back the button unchecked
        self.button_reset.set_checked(False,  block_events=True).enable()
        
    def _button_state_toggled(self, *a):
        """
        Update the state of the actuator. This calls self._update()
        """
        _debug('GUISingleActuator._button_state_toggled()')
        
        #Update
        self._update()
        #Put it back unchecked
        self.button_state.set_checked(False,  block_events=True).enable()
        
    def _button_move_toggled(self, *a):
        """
        Move the actuator to position set by the parameter Motion/Target_position
        """
        _debug('GUISingleActuator._button_move_toggled()')
        
        #Set the velocity
        v = self.settings['Motion/Speed'] #Extract the velocity from the parameters
        self.api.set_velocity(v)
        #Set the position
        r = self.settings['Motion/Target_position'] #Extract the position from the parameters
        self.api.set_position_abs(r)
        
        #Start to udpate
        self.timer_moving.start()
        
    def _button_stop_toggled(self, *a):
        """
        Stop the motion of the actuator !
        """
        _debug('GUISingleActuator._button_stop_toggled()')
        
        self.api.stop_motion()
        self._update() #udpate the state
        self.button_stop.set_checked(value=False) #Make it 'Clickable' again 
    
    def _update(self):
        """
        Update the information shown.
        """
        _debug('GUISingleActuator._update()')
        
        #Update only if the api exist
        if self.api != None: 
            #Update the position of the actuator.
            strpos = 'Position = ' + str(self.api.get_position()) + ' mm'
            self.label_position.set_text(strpos)
            _debug(strpos) 
            #Update the state         
            strState = 'State = ' + self.api.get_state()
            self.label_state.set_text(strState)
            _debug(strState) 
            
            #If the actuator doesn't move or is not homing. 
            cond1 = 'MOVING' == self.api.get_state()
            cond2 = 'HOMING' == self.api.get_state()
            if not(cond1 or cond2):
                #Stop to trigger the update with the timer
                self.timer_moving.stop()
                #Also uncheck the move button if there is not motion
                self.button_move .set_checked(False,  block_events=True).enable()
                
                
class GUIMagnet(egg.gui.Window):
    """
    Class that combines 3 actuator GUIs in order to control the position of the magnet.  
    """
    
    def __init__(self, name='Magnet', size=[1300,600]):
        """
        Create the GUI 
        """
        _debug('GUIMagnet.__init__()', name)
        _debug('Success is going from failure to failure without losing your enthusiasm – Winston Churchill')

        # Run the basic stuff for the initialization
        egg.gui.Window.__init__(self, title=name, size=size)
        
        # Remember the name. It is important a name, you know. 
        self.name = name
        
        #Save path to save file (useful when this GUI is inside probe_station)
        self.path_save_file = ''
                
        
        #Create the instance for the three actuator
        self.X = GUISingleActuator(show=False)
        self.X.settings['VISA/Device'] = 'COM5'
        self.X.set_name('Super-X')
        self.Y = GUISingleActuator(show=False)
        self.Y.settings['VISA/Device'] = 'COM4'
        self.Y.set_name('Mega-Y')
        self.Z = GUISingleActuator(show=False)
        self.Z.settings['VISA/Device'] = 'COM3'
        self.Z.set_name('Ultra-Z')

        # Add three actuator GUI
        self.place_object(egg.gui.Label('X: '), 0,0) #Set the label at position (0,0)
        self.place_object(self.X.window)
        self.new_autorow()
        self.place_object(egg.gui.Label('Y: '), 0,1) #Set the label at position (0,1)
        self.place_object(self.Y.window)
        self.new_autorow()
        self.place_object(egg.gui.Label('Z: '), 0,2) #Set the label at position (0,2)
        self.place_object(self.Z.window)
        
        # Place tabs for different task
        self.tabs1 = self.place_object(egg.gui.TabArea(), 
                                       row=0, column=1,
                                       column_span=5,  row_span=10,
                                       alignment=0)

        # Tab for sweeping lines
        self.gui_sweep_lines = GUIMagnetSweepLines(self)
        self.tab_sweep_lines = self.tabs1.add_tab('Sweep lines')
        self.tab_sweep_lines.place_object(self.gui_sweep_lines, alignment=0)   
        
        # Tab for the list sweep
        self.gui_list_sweep = GUIMagnetListSweep(self)
        self.tab_list_sweep = self.tabs1.add_tab('List sweep')
        self.tab_list_sweep.place_object(self.gui_list_sweep, alignment=0)  
        


        
    def go_to_xyz(self, x, y, z, want_wait=False):
        """
        Go to x, y, z (in mm)
        
        want_wait:
            (boolean) Weither of not we want to wait before it finishes
        """
        _debug('GUIMagnet: go_to_xyz'  )
               
        # Set the target positions
        self.X.settings['Motion/Target_position'] = x
        self.Y.settings['Motion/Target_position'] = y
        self.Z.settings['Motion/Target_position'] = z       
        
        # Go for real
        self.X.button_move.click()
        self.Y.button_move.click()
        self.Z.button_move.click()

        if want_wait:
            #Wait that the actuators finished to move. 
            condition = True
            while condition:
                # Wait for not exploding the CPU
                time.sleep(0.1)
                 #Allow the GUI to update. This is important to avoid freezing of the GUI inside loop
                self.process_events()
                # Note the condition for keeping doing
                # As long as the three actuator move
                condition1 = self.X.api.get_state() == 'MOVING'
                condition2 = self.Y.api.get_state() == 'MOVING'
                condition3 = self.Z.api.get_state() == 'MOVING'
                condition = condition1 or condition2 or condition3
            


class GUIMagnetSweepLines(egg.gui.Window):
    """
    Gui for making the actuator to sweep along various lines
    """
    #TODO Rewrite it and make sure that it does what it should.
    
    def __init__(self, magnet3, name='Magnet sweep lines', show=True,size=[1300,600]):
        """
        Create the GUI 
        
        magnet3:
            The gui object "GUIMagnet" that is used to control the three 
            actuators. 
        """
        _debug('GUIMagnetSweepLines: __init__', name)
        _debug('The best way to predict your future is to create it. – Abraham Lincoln')
        
        self.X = magnet3.X
        self.Y = magnet3.Y
        self.Z = magnet3.Z
        
        # Run the basic stuff for the initialization
        egg.gui.Window.__init__(self, title=name, size=size)
        
        #Add a button for loading the data
        self.button_load_list   = self.place_object(egg.gui.Button('Load list', checkable=True), 2,0).set_width(100)
        self.connect(self.button_load_list.signal_clicked, self.button_load_list_clicked )

        #Add a button for loading the data
        self.button_test  = self.place_object(egg.gui.Button('Prepare'), 2,1)
        self.connect(self.button_test.signal_clicked, self.button_test_clicked )
        
        
        self.button_scan_magnet = self.place_object(egg.gui.Button('Scan Magnet', checkable=True), 3,1).set_width(150)
        self.button_scan_magnet.signal_toggled.connect(self.button_scan_magnet_clicked)   
        
        # Add a label
        self.label_load_file    = self.place_object(egg.gui.Label('No File loaded ;)'), 3,0 )


    def button_test_clicked(self):
        """
        Test to generate the data for scanning. 
        """
        
        self.databox = _s.data.databox()
        self.databox.insert_header('name', 'Hakuna matata')
        
        # Add each column
        self.databox['xs'] = np.linspace(0, 4, 13)
        self.databox['ys'] = np.linspace(0, 4, 13)+1
        self.databox['zs'] = np.linspace(0, 4, 13)*0+13
        
        
        
    def button_load_list_clicked(self, *a):
        """
        Load a list of x,y,z points for the magnetic field sweep
        """
        _debug('GUIMagnetSweepLines._button_load_list_toggled()')
        
        #Load the list. 
        self.d = _s.data.load(text='Load the set of lines to sweep')
        #Set the text. If sucess, the text is the name of the file. Otherwise it is an error message. 
        self.label_load_file.set_text( self.fill_table_positions(self.d) )
        #Uncheck the button
        self.button_load_list  .set_checked(False,  block_events=True).enable()

    def scan_xyz_line(self, xend=0, yend=0, zend=0, speed=1, N=10):
        """
        Move in a straight line from the current position to the target position. 
        
        xend:
            (in mm) Target x position
        yend:
            (in mm) Target y position
        zend:
            (in mm) Target z position    
        speed:
            (in mm/sec) Speed of the displacement along the line
        N:
            Number of points to record
        """
        _debug('GUIMagnetSweepLines: scan_xyz_line')
        
        self.xend = xend
        self.yend = yend
        self.zend = zend
        # Set the target positions
        self.X.settings['Motion/Target_position'] = xend
        self.Y.settings['Motion/Target_position'] = yend
        self.Z.settings['Motion/Target_position'] = zend
        
        # Find the speed of each actuator for them to reach the end at the same 
        # time
        # We need to know the distance that they will have to travel 
        self.xin = self.X.api.get_position()
        self.yin = self.Y.api.get_position()
        self.zin = self.Z.api.get_position()
        self.dx = np.abs(self.xin - xend)
        self.dy = np.abs(self.yin - yend)
        self.dz = np.abs(self.zin - zend)
        ds = np.sqrt(self.dx**2 + self.dy**2 + self.dz**2) # Total distance to travel
        self.T = ds/speed # Total time for making the displacement
        # Now determine the speed along each axis
        self.vx = self.dx/self.T
        self.vy = self.dy/self.T
        self.vz = self.dz/self.T
        self.X.settings['Motion/Speed'] = self.vx
        self.Y.settings['Motion/Speed'] = self.vy
        self.Z.settings['Motion/Speed'] = self.vz
        
        # This will store the positions of the actuator
        self.xs = []
        self.ys = []
        self.zs = []
        self.dt = self.T/N # How much time to wait between points
         #Allow the GUI to update. This is important to avoid freezing of the GUI inside loop
        self.process_events()        
        
        # Go !
        # Let's take the positions
        self.xs.append( self.X.api.get_position() )
        self.ys.append( self.Y.api.get_position() )
        self.zs.append( self.Z.api.get_position() )
        # Go for real
        self.X.button_move.click()
        self.Y.button_move.click()
        self.Z.button_move.click()
        
        # Note the condition for keeping doing
        # As long as the three actuator move
        condition1 = self.X.api.get_state() == 'MOVING'
        condition2 = self.Y.api.get_state() == 'MOVING'
        condition3 = self.Z.api.get_state() == 'MOVING'
        condition = condition1 or condition2 or condition3
        while condition:
            # wait the desired interval of time
            time.sleep(self.dt)
            # Let's take the positions
            self.xs.append( self.X.api.get_position() )
            self.ys.append( self.Y.api.get_position() )
            self.zs.append( self.Z.api.get_position() )
             #Allow the GUI to update. This is important to avoid freezing of the GUI inside loop
            self.process_events()
            
            # Call a signal
            self.event_scan_line_checkpoint()
            
            # Note the condition for keeping doing
            # As long as the three actuator move
            condition1 = self.X.api.get_state() == 'MOVING'
            condition2 = self.Y.api.get_state() == 'MOVING'
            condition3 = self.Z.api.get_state() == 'MOVING'
            condition = condition1 or condition2 or condition3
        
        _debug('GUIMagnetSweepLines: scan_xyz_line: Done')
        
    def event_scan_line_checkpoint(self):
        """
        Dummy function to be overrid. 
        This is done when we scan a straight line, each time that we reach a
        point to record.
        """
        
    def button_scan_magnet_clicked(self, *a):
        """
        Move the actuator at each x,y,z position loaded in the table self.table_positions
        Perfom something at each of these position. We have to thing more about how to implement this within the master GUI. 
        """
        _debug('GUIMagnetSweepLines.button_scan_magnet_clicked')
        self.scan_xyz_line(20.5, 9.3, 17.7, speed=1, N=5)
        
        
class GUIMagnetListSweep(egg.gui.Window):
    """
    Gui for making the actuator to go at each position in the list and perform 
    a task at each single position.
    """
    #TODO Rewrite it and make sure that it does what it should.
    #TODO FOr example, exctrat X, Y and Z components of magnet3
    
    def __init__(self, magnet3, name='Magnet sweep list', show=True, size=[1300,600]):
        """
        Create the GUI 
        
        magnet3:
            The gui object "GUIMagnet" that is used to control the three actuator. 
        """
        _debug('GUIMagnetListSweep: __init__', name)
        _debug('Don’t watch the clock; do what it does. Keep going. – Sam Levenson')
        
        # Run the basic stuff for the initialization
        egg.gui.Window.__init__(self, title=name, size=size)
        
        #Add other objects
        self.button_load_list   = self.place_object(egg.gui.Button('Load list', checkable=True), 2,0).set_width(100).disable()
        self.button_scan_magnet = self.place_object(egg.gui.Button('Scan Magnet', checkable=True), 3,1).set_width(150).disable()
        self.label_load_file    = self.place_object(egg.gui.Label('No File loaded ;)'), 3,0 )
        self.table_positions    = self.place_object(egg.gui.Table(columns = 3, rows = 5), 2,1) #Table containing the xyz position of the magnet
        
        #Connect the button !
        self.button_load_list  .signal_toggled.connect(self._button_load_list_toggled)
        self.button_scan_magnet.signal_toggled.connect(self._button_scan_magnet_toggled)   
        
        #Enable the button
        self.button_load_list  .set_checked(False,  block_events=True).enable()
        self.button_scan_magnet.set_checked(False,  block_events=True).enable()
#        
#        self.table_positions._widget.cellClicked(1,1)        
        

    def _button_load_list_toggled(self, *a):
        """
        Load a list of x,y,z points for the magnetic field sweep
        """
        _debug('GUIMagnetListSweep._button_load_list_toggled()')
        
        #Load the list. 
        self.d = _s.data.load(text='Load list of x,y,z positions ;)', filters="*.csv")
        
        #Set the text. If sucess, the text is the name of the file. Otherwise it is an error message. 
        self.label_load_file.set_text( self.fill_table_positions(self.d) )
        
        #Uncheck the button
        self.button_load_list  .set_checked(False,  block_events=True).enable()
        
        
    def _button_scan_magnet_toggled(self, *a):
        """
        Move the actuator at each x,y,z position loaded in the table self.table_positions
        Perfom something at each of these position. We have to thing more about how to implement this within the master GUI. 
        """
        _debug('GUIMagnetListSweep._button_scan_magnet_toggled')
        

        
        # Only run the sweep if we have enabled the button
        if self.button_scan_magnet.is_checked():
            
            
            #Ask a path to save anything
            self.path_save_file = _s.dialogs.select_directory(text='Select Directory to save datas' )
            
            #Disable the load of file, because loading a file while scanning would be sad. 
            self.button_load_list.disable()
            
            #Note how much scan will be perfomed. 
            nbScan = self.table_positions.get_row_count() 
            #Update the text on the button
            self.button_scan_magnet.set_height(50)
            self.button_scan_magnet.set_text('Scanning over %d positions...\nClick to STOP !'%nbScan)
            
            #Start the scan.
            for i in range (nbScan):
                
                #Break out if cancel. 
                if not self.button_scan_magnet.is_checked(): 
                    #Stop the actuators !
                    self.X.button_stop.click()
                    self.Y.button_stop.click()
                    self.Z.button_stop.click()
                    break
                
                #Move ! The function waits that the actuator stop to move before keeping goinf. 
                self.go_to(self.X, column=0, row=i)
                self.go_to(self.Y, column=1, row=i)
                self.go_to(self.Z, column=2, row=i)
                
                #Allow the GUI to update. This is important to avoid freezing of the GUI inside loop
                self.window.process_events() 
                
                #Perfom a task on the i'th row
                # This is where you could insert some interesting code.
                self.after_scan_set_positions(i)
            
            #Enable back buttons and update their "checkability" lol 
            self.button_load_list  .set_checked(False,  block_events=True).enable()
            self.button_scan_magnet.set_checked(False,  block_events=True)
            self.button_scan_magnet.set_height(25)
            self.button_scan_magnet.set_text('Scan Magnet')
            
    def fill_table_positions(self, data):
        """
        Fill up self.table_positions with the three first columns of data. 
        The three first columns of data must have the same lenght. 
        
        Return a string being:
            The name of the file if it succed OR
            An error message corresponding to what happened. 
        """
        _debug('GUIMagnetListSweep.fill_table_positions()')
        
        #Try to open the data
        try: 
            #First check if the lenghts matche
            if not (len(data[0]) == len(data[1])):
                return 'Lenght of first and second columns do not match !'
            if not (len(data[1]) == len(data[2])):
                return 'Lenght of second and third columns do not match !'  
            if not (len(data[2]) == len(data[0])):
                return 'Lenght of first and third columns do not match !' 
            
            #If we pass here, we are ready to extract the position from the data 
            #First destroy the previous table
            while (self.table_positions.get_row_count() > 0):
                self.table_positions._widget.removeRow(0)
                
            #Then input the new one. 
            for i in range( len(data[0]) ):
                #Extract the x position 
                self.table_positions.set_value(column=0, row=i, value=data[0][i])
                #Extract the y position 
                self.table_positions.set_value(column=1, row=i, value=data[1][i])                
                #Extract the z position 
                self.table_positions.set_value(column=2, row=i, value=data[2][i])   
            
            self.label_load_file.set_colors(text='black',background=None)
            return data.path.split()[-1]
            
        except: 
            self.label_load_file.set_colors(text='red',background=None)
            return 'Error in reading the data from the file :S '
        
    def go_to(self, actuator, column =0, row =0):
        """
        Make the actuator go to the position in the (column, row) in the table. 
        - acturator = _actuator.actuator() object (ie, self.X, self.Y or self.Z) 
                      that we want to move. 
        - column    = column to read in self.table_positions
        - row       = row to read in self.table_positions
        
        The function wait that the actuator finish to move. 
        
        Possible upgrade: Make the three actuators to move at the same time. 
                          Then wait that the three actuator finish to move. 
        
        """
        _debug('GUIMagnetListSweep.go_to()', actuator, column, row)
        
        #Set the target position
        r = self.table_positions.get_value(column=column, row=row)
        actuator.settings['Motion/Target_position'] = r
        #Update the information on the GUI
        self.window.process_events()
        
        #Make it move !
        actuator.button_move.click()
        #Wait that the actuator finished to move. 
        while actuator.api.get_state() == 'MOVING':
            #Wait a little bit to not explode the processor. 
            time.sleep(0.1)
            #Allow the GUI to update. This is important to avoid freezing of the GUI inside loop
            self.window.process_events()
            #Update the position and state.
            actuator._update()
        if not 'READY' in actuator.api.get_state():
            print('WARNING ! Actuator ' + actuator.get_name() + 'Is not in Ready State')
        return

    def go_to_xyz(self, x, y, z, want_wait=False):
        """
        Go to x, y, z (in mm)
        
        want_wait:
            (boolean) Weither of not we want to wait before it finishes
        """
        
        # Set the target positions
        self.X.settings['Motion/Target_position'] = x
        self.Y.settings['Motion/Target_position'] = y
        self.Z.settings['Motion/Target_position'] = z       
        
        # Go for real
        self.X.button_move.click()
        self.Y.button_move.click()
        self.Z.button_move.click()

        if want_wait:
            #Wait that the actuators finished to move. 
            condition = True
            while condition:
                # Wait for not exploding the CPU
                time.sleep(0.1)
                 #Allow the GUI to update. This is important to avoid freezing of the GUI inside loop
                self.window.process_events()
                # Note the condition for keeping doing
                # As long as the three actuator move
                condition1 = self.X.api.get_state() == 'MOVING'
                condition2 = self.Y.api.get_state() == 'MOVING'
                condition3 = self.Z.api.get_state() == 'MOVING'
                condition = condition1 or condition2 or condition3
                
    def after_scan_set_positions(self, i=0):
        """
        Task to perfom at the position corresponding to the i'th row of
        self.table_position.
        
        To overwrite for doing stuff like GHz sweep or anything ;)
        i is the iteration in the table (the i'th row), such that we can perform 
        a task depending on the iteration. 
        """
        _debug('GUIMagnetListSweep: after_scan_set_positions', i)
        
        print('On the %dth row ;)'%i)        


#By default set the object
if __name__ == '__main__':
    _debug_enabled = True
    import api_actuator
    api_actuator._debug_enabled
    
#    cc = ApiActuator().
    self = GUIMagnet(name='Magnetooooo') 
    self.show()
    
#    # Check the trajectory 
#    from mpl_toolkits.mplot3d import Axes3D # This import registers the 3D projection, but is otherwise unused.
#    import matplotlib.pyplot as plt
##    fig = plt.figure()
##    ax = fig.add_subplot(111, projection='3d')   
##    ax.scatter(self.xs[1:-1], self.ys[1:-1], self.zs[1:-1]) 
##    ax.scatter(self.xs[0], self.ys[0], self.zs[0], color='red',label='First')
##    ax.scatter(self.xs[-1], self.ys[-1], self.zs[-1], color='y',label='End')
##    ax.plot([self.xin,self.xend], [self.yin,self.yend], [self.zin,self.zend], label='Goal')
##    plt.legend()
##    ax.set_xlabel('x (mm)')
##    ax.set_ylabel('y (mm)')
##    ax.set_zlabel('z (mm)')
##    # Set equal aspect
##    # First get the extermum of all the pts
##    allpts = np.concatenate((self.xs, self.ys, self.zs))
##    maximum = np.max(allpts)
##    minimum = np.min(allpts)
##    ax.set_xlim3d(minimum, maximum)
##    ax.set_ylim3d(minimum, maximum)
##    ax.set_zlim3d(minimum, maximum)
#    
#    # Test many scan
#    xtots = []
#    ytots = []
#    ztots = []
#    # Try a plane
#    x1 = 10
#    x2 = 17
#    z1 = 15
#    z2 = 22
#    ys = np.linspace(14, 19, 10)
#    # First reach the initial position
#    self.go_to_xyz(x1, ys[0], z1, want_wait=True)
#    for i in range(int(len(ys)/2)):
#        y1 = ys[2*i]
#        y2 = ys[2*i+1]
#        # Make a zigzage following the y axis
#        self.scan_xyz_line(x2, y2, z2, speed=1, N=40)
#        xtots.extend(self.xs)
#        ytots.extend(self.ys)
#        ztots.extend(self.zs)
#        self.scan_xyz_line(x1, y1, z1, speed=1, N=40)
#        xtots.extend(self.xs)
#        ytots.extend(self.ys)
#        ztots.extend(self.zs)
#        
#    fig = plt.figure()
#    ax = fig.add_subplot(111, projection='3d')   
#    ax.scatter(xtots, ytots, ztots) 
#    ax.scatter(xtots[0], ytots[0], ztots[0], color='red',label='First')
#    ax.scatter(xtots[-1], ytots[-1], ztots[-1], color='y',label='End')
#    plt.legend()
#    ax.set_xlabel('x (mm)')
#    ax.set_ylabel('y (mm)')
#    ax.set_zlabel('z (mm)')
#    # Set equal aspect
#    # First get the extermum of all the pts
#    allpts = np.concatenate((xtots, ytots, ztots))
#    maximum = np.max(allpts)
#    minimum = np.min(allpts)
#    ax.set_xlim3d(minimum, maximum)
#    ax.set_ylim3d(minimum, maximum)
#    ax.set_zlim3d(minimum, maximum)    
#    
    
    
    
#    # Old scan
#    self.scan_xyz_line(20.5, 9.3, 17.7, speed=1, N=40)
#    xtots.extend(self.xs)
#    ytots.extend(self.ys)
#    ztots.extend(self.zs)
#    self.scan_xyz_line(14, 9.4, 10, speed=1, N=40)
#    xtots.extend(self.xs)
#    ytots.extend(self.ys)
#    ztots.extend(self.zs)
#    self.scan_xyz_line(17, 14, 17.7, speed=1, N=40)
#    xtots.extend(self.xs)
#    ytots.extend(self.ys)
#    ztots.extend(self.zs)   
    
    
    
    