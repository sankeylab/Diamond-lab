# -*- coding: utf-8 -*-
"""
Created on Fri Aug  7 10:19:41 2020

@author: Childresslab
"""

import numpy as np
import simpleaudio as sa


class sound():
    """
    An object for playing sound each time we call the methods "play" 
    """
    
    def __init__(self, fs=44100):
        """
        fs:
            sampling rate, Hz, must be integer.
        """
        self.fs = fs

    
    def play_wobble(self,Hz, Hz_modulation=0.5, duration=1.0, volume=0.5):
        """
        A sine modulated... by a sine !
        
        Hz:
            Frequency to be played.
        Hz_modulation:
            Modulation of the sine wave
        duration:
            In seconds, may be float
        volume:
            The volume. range [0.0, 1.0]   
        """

        N = self.fs*duration # Number of point to sample
        t = 2*np.pi*np.arange(N)/self.fs # Time axis
        
        # Define the sound
        sine = np.sin(t*Hz)
        modulation = np.sin(t*Hz_modulation)
        
        audio = ((1+sine)*modulation/2).astype(np.float32)
        
        # normalize to 16-bit range
        audio *= 32767 / np.max(np.abs(audio))
        # convert to 16-bit data
        audio = audio.astype(np.int16)
        
        # start playback
        self.play_obj = sa.play_buffer(audio, 1, 2, self.fs)
        
#        # wait for playback to finish before exiting
#        play_obj.wait_done()
        



    def play_ringdown(self,Hz, duration=1.0, volume=0.5):
        """
        A decaying sine. The time scale is the duration
        
        Hz:
            Frequency to be played.
        Hz_modulation:
            Modulation of the sine wave
        duration:
            In seconds, may be float
        volume:
            The volume. range [0.0, 1.0]   
        """

        N = self.fs*duration # Number of point to sample
        t = 2*np.pi*np.arange(N)/self.fs # Time axis
        
        # Define the sound
        sine = np.sin(t*Hz)
        modulation = np.exp(-t/duration)
        
        audio = ((1+sine)*modulation/2).astype(np.float32)
        
        # normalize to 16-bit range
        audio *= 32767 / np.max(np.abs(audio))
        # convert to 16-bit data
        audio = audio.astype(np.int16)
        
        # start playback
        self.play_obj = sa.play_buffer(audio, 1, 2, self.fs)
        
    
if __name__=="__main__":
    
    self = sound()
    
    self.play_wobble(1000, 5, duration=5)
    print('Hello')
    self.play_wobble(550, 5, duration=5)
    print('Hey')
    
    self.play_wobble(440, 0.5, duration=10)
    print('Heyhey')    
    
#    self.play_ringdown(440, duration=10)
    