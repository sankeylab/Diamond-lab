# -*- coding: utf-8 -*-
"""
Created on Mon Jun 22 11:01:38 2020

Create a base class for all the protocols

@author: Michael
"""

import numpy as np

#import experiment

_debug_enabled = False #Set to true for printing debugging stuff
def _debug(*a):
    """
    Debugging function that we can insert anywhere. 
    """
    if _debug_enabled: 
        s = []
        for x in a: s.append(str(x))
        print(', '.join(s))


class Protocol():
    """
    This a parent class for all the protocols that we are testing 
    for the T1 measurements. 
    
    It contains the attributes and method which are common to all the 
    type of protocols that we want to compare. 
    
    
    """
    
    def __init__(self, model_functions, constants):
        """
        model_functions = [f0, fp, fm]
        constants = [PL0, contrast]
        
        f0,fp,fm:
            Function with signature (t,Gp,Gm) which gonna define the PL for the 
            three type of measurement. Those are amoung the 9 in the model. 

        PL0:
            Mean photocounts from the ms=0 state. 
        contrast:
            Contrast in photoluminescence from the ms=+-1 state. This is 
            defined such that the photoluminescence coming from ms=+-1 is 
            PL0*(1-contrast)      
                     
            
        """
        _debug('Protocol: __init__')
        _debug('I never lose. Either I win or learn. – Nelson Mandela')
        self.model_functions = model_functions
        
        self.f0 = model_functions[0]
        self.fp = model_functions[1]
        self.fm = model_functions[2]
        
        self.constants = constants
        
        
        
        #Variable to be stock for studying the protocol
        #Times
        self.t_probe_p_s          = []  # Times for measuring f0-fp     
        self.t_probe_m_s          = []  # Times for measuring f0-fm  
        
        self.t_pulseSequences_s = []  #This will store the  times elapsed in the pulse sequences for an individual iteration
        self.t_process_s        = []  #This will store the  times elapsed in the CPU processing for an individual iteration        
        self.t_pulseSequences   = 0 #Time elapsed in the pulse sequences for an individual iteration
        self.t_process          = 0  #Time elapsed in the CPU processing for an individual iteration  
        #Total, accumulated, times
        self.t_tot_pulseSequences_s = []   #This will store the total times elapsed for the pulse sequences
        self.t_tot_process_s        = []  #This will store the total CPU times elapsed for processing the Bayes stuffs
        self.t_tot_pulseSequences   = 0 #Total times elapsed for the pulse sequences
        self.t_tot_process          = 0 #Total CPU time elapsed so far for processing the Bayes stuffs
        #Stuff on the rates
        self.Gp_guess_s   = []  #Mean of gamma+ from the posterior
        self.Gm_guess_s   = []  #Mean of gamma- from the posterior
        self.eGp_guess_s  = []  #Standard deviation of gamma+ from the posterior
        self.eGm_guess_s  = []  #Standard deviation of gamma- from the posterior        
        self.cov_Gp_s    = []  #Variance of gamma+ from the posterior
        self.cov_Gm_s    = []  #Variance of gamma- from the posterior
        self.cov_GpGm_s  = []  #Covariance of gamma- & gamma- from the posterior    
        
        #Other
        self.nb_iteration_s = [] #Stock the number of iteration done so far
        self.R_tot_s        = [] #Stock Total numbers of readout performed so far
        self.R_tot           = 0 #Total number of readout for performed so far
        
        self.iter = 0 #Iterator

    def measure_3PL(self, t_probe, R):
        """
        Measure the 3 photoluminescence at the same time. 
        Get the difference diffp=f0-fp, diffm=f0-fm and the associated error 
        and correlation.
        
        Perform a measurement to extract "results", which is a tuple:
            (t_tot, diff_p, diff_m, ediff_p, ediff_m, corr, R_tot)
            
        R:
            Number of readout to perform for each individual measure of the ms state.                  
        """
        _debug('Protocol: measure_3PL')
        
        self.t_probe = t_probe
        self.measure_type = '3PL' # This is useful for knowing what to store

        # 3 measures
        exp = experiment.Experiment(self.model_functions, self.constants)
        self.results = exp.diff_PC_3measure(self.t_probe,  R) 
        
        # Extract the results
        self.diff_p  = self.results[1]
        self.diff_m  = self.results[2]
        self.ediff_p = self.results[3]
        self.ediff_m = self.results[4]
        self.corr    = self.results[5]  # Should be zero in the case of 4 independant measurements.  
        
        _debug('Protocol: measure_3PL: Diffp = %f +- %f'%(self.diff_p, self.ediff_p))   
        _debug('Protocol: measure_3PL: Diffm = %f +- %f'%(self.diff_m, self.ediff_m))
             
        # Update the total number of readout performed with this type of measurement
        self.R_tot = self.results[6] 
        # Note the time for the pulse sequence
        self.t_pulseSequences = self.results[0]   
        
        
    def measure_4PL(self, tp, tm, R):
        """
        Measure the PL of 
        Get the difference diffp=f0-fp, diffm=f0-fm and the associated error 
        and correlation.
        
        Perform a measurement to extract "results", which is a tuple:
            (t_tot, diff_p, diff_m, ediff_p, ediff_m, corr, R_tot)
            
        R:
            Number of readout to perform for each individual measure of the ms state.                  
        """
        _debug('Protocol: measure_4PL')
        
        self.tm, self.tp = tp, tm
        self.measure_type = '4PL' # This is useful for knowing what to store

        # 3 measures
        exp = experiment.Experiment(self.model_functions, self.constants)
        self.results = exp.diff_PC_4measure(self.tm, self.tp,  R) 
        
        # Extract the results
        self.diff_p  = self.results[1]
        self.diff_m  = self.results[2]
        self.ediff_p = self.results[3]
        self.ediff_m = self.results[4]
        self.corr    = self.results[5]  # Should be zero in the case of 4 independant measurements.  
        
        _debug('Protocol: measure_4PL: Diffp = %f +- %f'%(self.diff_p, self.ediff_p))   
        _debug('Protocol: measure_4PL: Diffm = %f +- %f'%(self.diff_m, self.ediff_m))
             
        # Update the total number of readout performed with this type of measurement
        self.R_tot = self.results[6] 
        # Note the time for the pulse sequence
        self.t_pulseSequences = self.results[0]   


    def store_info(self):
        """
        Append the actual information into lists. 
        """
        _debug('Protocol: store_info' )  
        
        #Times
        if self.measure_type == '3PL':
            self.t_probe_p_s       .append(self.t_probe) 
            self.t_probe_m_s       .append(self.t_probe) 
        if self.measure_type == '4PL':
            self.t_probe_p_s       .append(self.tp) 
            self.t_probe_m_s       .append(self.tm) 
            
        self.t_pulseSequences_s.append(self.t_pulseSequences)
        self.t_process_s       .append(self.t_process)
        #Total, accumulated, times
        self.t_tot_pulseSequences_s.append(self.t_tot_pulseSequences) 
        self.t_tot_process_s       .append(self.t_tot_process)  
        #Rates
        self.Gp_guess_s  .append(self.Gp_guess)  #Mean of gamma+ 
        self.Gm_guess_s  .append(self.Gm_guess)  #Mean of gamma- 
        self.eGp_guess_s .append(self.eGp_guess)  #Uncertainty of gamma+
        self.eGm_guess_s .append(self.eGm_guess) #Uncertainty of gamma-   
        self.cov_GpGm_s  .append(self.cov_GpGm)  #Covariance of gamma- & gamma-   
        #Other
        self.nb_iteration_s.append(self.iter)
        self.R_tot_s       .append(self.R_tot)
            
    def get_results(self):
        """
        Return the stored important results of the simulation so far, in the form of dictionary. 
        The information in the dictionary are the objects updated from the method
        self.store_int()
        
        This should be a common for each type of simulation. The objects that 
        are common in the dictionnary of different simulation should have the 
        same key (for example, the best guesses for gamma+ should always have 
        the key 'Gp_s'). This would allow a generally access to these object 
        for an arbitrarly simulation.
        """
        r ={
            'Gp_s' :np.array(self.Gp_guess_s), #Means of the posteriors
            'Gm_s' :np.array(self.Gm_guess_s), #Means of the posteriors
            'eGp_s':np.array(self.eGp_guess_s) , #Standard deviations of the posteriors
            'eGm_s':np.array(self.eGm_guess_s) , #Standard deviations of the posteriors
            'covGpGm_s':np.array(self.cov_GpGm_s) , #Covariances of the posteriors
            't_tot_pulseSequences_s':np.array(self.t_tot_pulseSequences_s), #Time it takes for each batch of pulse sequences
            't_tot_process_s':np.array(self.t_tot_process_s), #CPU time it takes for processing the Bayes stuff at each iteration
            't_probe_p_s':np.array(self.t_probe_p_s), # Times probed for the diff p
            't_probe_m_s':np.array(self.t_probe_m_s), # Times probed for the diff m
            't_pulseSequences_s':np.array(self.t_pulseSequences_s),
            't_process_s':np.array(self.t_process_s),
            'iteration_s':np.array(self.nb_iteration_s), #Number of iterations performed
            'R_tot_s':np.array(self.R_tot_s) #Total number of readout performed
            }
        return r







if __name__ == '__main__': 
    _debug_enabled = True
    # Load the model
    import model
    # Define the constants
    PL0      = 0.04
    contrast = 0.2
    constants = [PL0, contrast]
    
    # Define the model that we want to check
    f0 = model.PLModel(constants).PLpm
    fp = model.PLModel(constants).PLpp
    fm = model.PLModel(constants).PLmm
    model_functions = [f0, fp, fm]
    
    self = Protocol(model_functions, constants)
    self.measure_3PL(2e-6, 1000)
    self.store_info()
    res = self.get_results()








        
        


