# -*- coding: utf-8 -*-
"""
Created on Tue Apr 21 16:36:39 2020

Goal: Implement the Bayes protocole in object.

@author:  Micky-mike
"""



import numpy as np
import time 
from scipy import interpolate # Useful for the rediscretization of the domain
from scipy.optimize import minimize # For some method for determining the best time to probe

import matplotlib.pyplot as plt 


from protocol_baseclass import Protocol



_debug_enabled = False #Set to true for printing debugging stuff
def _debug(*a):
    """
    Debugging function that we can insert anywhere. 
    """
    if _debug_enabled: 
        s = []
        for x in a: s.append(str(x))
        print(', '.join(s))


        
def integral_2D(x,y, Z):
    """
    Integrate in 2 dimension Z. 
    Z is the 2D array to integrate. 
    x and y are both 1D array used to define the axis of Z
    """
    _debug('integral2D')#,
#               'x:', x,
#               'y:', y,
#               'Z:', Z)
    firstInt = np.trapz(Z, x=x, axis=1) #First integrate along the first axis
    return     np.trapz(firstInt, x=y) #Integrate over the remaining axis



class Bayes3Measure(Protocol):
    """
    Bayes protocol for 3 measure
    Simulate the experiment with the bayes approach to infer the best 
    estimate of the rates. 
    
    For this class, we gonna hit on the same point (Non-adaptive).     
     
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
        _debug('Bayes3Measure: __init__')
        _debug('Your limitation-it’s only your imagination.')
        
        # Python also has a super() function that will make the child class inherit all the methods and properties from its parent
        super().__init__(model_functions, constants)
       
        self.model_functions = model_functions        
        self.f0 = model_functions[0]
        self.fp = model_functions[1]
        self.fm = model_functions[2]
        
        # For now the constants are just used for taking measurement, because
        # they are not taken into account 
        self.constants = constants
        
    def __repr__(self):
        """
        Returns the string that appears when you inspect the object.
        """
        s  = '\nBayesSameTimes object'
        s += '\n'
        try:
            s += '\nNb readout = %d'%self.R
            s += '\nGuess: Gp = %f kHz'%(self.Gp_guess*1e-3)
            s += '\nGuess: Gm = %f kHz'%(self.Gm_guess*1e-3)
            s += '\n'
            s += '\nsqrt(cov_Gp) = %f kHz'%(np.sqrt(self.cov_Gp)*1e-3)
            s += '\nsqrt(cov_Gm) = %f kHz'%(np.sqrt(self.cov_Gm)*1e-3)
            s += '\nAdd other stocks ;)'
        except:
            s += '\nNot everything is computed yet'
        print(s)

    def get_likelihood_3measure(self, exp0, expp, expm, diffp, diffm):   
        """
        Update the likehihood, from the knowledge of the cumulated measurement
        
        TODO Epxlain the inputs
            
        """
        _debug('Bayes3Measure: get_likelihood_3measure')
        # Precompute arrays for simplification
        ZZZ = expp*expm +exp0*(expp+expm)
        
        A = (exp0 + expp + expm +2*(diffp+diffm) 
            + diffp*diffp/expp + diffm*diffm/expm )
        
        B = (expp*diffm + expm*(3*expp+diffp))**2       
        C = exp0/(expp*expm*ZZZ)
        # THE like-lihood
        L = 0.5*(np.log(ZZZ) + A - B*C )
        
        return L  
            
    def update_post(self):
        """
        Update the posterior. 
        Compute it from the like-lihood and the prior, than normalize it
        """
        _debug('Bayes3Measure: update_post' )
            
        #Get the posterior from the like-lihood and the prior
        self.Ppost  = np.exp(-self.L)*self.prior
        self.Ppost /= self.integral2D(self.gp_axis, self.gm_axis, self.Ppost) #Normalize 
        if _debug_enabled:
            #Put this debug into an extra of, because the extra calculation of the volume might be expensive 
            _debug('Volume of posterior (its not fun)  = ', self.integral2D(self.gp_axis, self.gm_axis, self.Ppost ) )    
   

    def compute_variance(self, method='integral'):
        """
        Computhe the variance the the posterior. 
        method:
            string 
        """
        if method =='integral':
            # Simplify the integral by first calculate the second orde moements
            mean_Gp2  = self.integral2D(self.gp_axis, self.gm_axis, self.Ppost*(self.Gp_Axis*self.Gp_Axis)) 
            mean_Gm2  = self.integral2D(self.gp_axis, self.gm_axis, self.Ppost*(self.Gm_Axis*self.Gm_Axis)) 
            mean_GpGm = self.integral2D(self.gp_axis, self.gm_axis, self.Ppost*(self.Gp_Axis*self.Gm_Axis)) 
            # From the moments, get the covariances
            self.cov_Gp   = mean_Gp2  - self.Gp_guess*self.Gp_guess
            self.cov_Gm   = mean_Gm2  - self.Gm_guess*self.Gm_guess
            self.cov_GpGm = mean_GpGm - self.Gp_guess*self.Gm_guess            
        
    def process_post(self, method='mix'):
        """
        Process the posterior. 
        Estimate the rates and the covariance matrix element from the 
        posterior pdf. 
        
        method:
            String defining which way to extract the mean, variance, 
            correlation, etc. 
        
        """    
        _debug('Bayes3Measure: process_post' )       
        
        #Update the posterior
        self.update_post() # Will update only if it hasn't be done before
       
        if method == 'integral':
            """
            Integrate the posterior with the corresponding weights for 
            extractiong quantities. 
            """
            _debug('Integral')
            #Get the expected mean for both rates
            #Integrate in 2D. 
            self.Gp_guess  = self.integral2D(self.gp_axis, self.gm_axis, self.Ppost*self.Gp_Axis)
            self.Gm_guess  = self.integral2D(self.gp_axis, self.gm_axis, self.Ppost*self.Gm_Axis)
            #Get the covariant matrix element
            self.compute_variance()
        
        elif method == 'parabola':
            """
            Take second derivative around the maximum for estimating the 
            variance. 
            """       
            _debug('Parabola')
            # Take the maximum of the posterior for the best estimate
            # Use the logarithm of the posterior, to ease the calculation
            self.logP = -np.log(self.Ppost) # DO NOT take self.L, because we also need the prior
            # Get the indices of the minimum 
            shape = self.logP.shape
            self.ind = np.unravel_index(self.logP.argmin(), shape)
            i = self.ind[0]
            j = self.ind[1]

            if i==0:
                i = 1
            if i == shape[0]-1:
                i -= 1            
            if j==0:
                j = 1
            if j == shape[1]-1:
                j -= 1         
                
            self.Gp_guess = self.Gp_Axis[i][j]  # The mean is for if there are more than one max
            self.Gm_guess = self.Gm_Axis[i][j] 
          
            # Second derivative in the direction of gamma+
            dGp = self.Gp_Axis[i][j+1] - self.Gp_Axis[i][j]
            A = (self.logP[i][j+1]+self.logP[i][j-1]-2*self.logP[i][j])/(dGp*dGp) 
            # Second derivative in the direction of gamma-
            dGm = self.Gm_Axis[i+1][j+1] - self.Gm_Axis[i][j]
            B = (self.logP[i+1][j]+self.logP[i-1][j]-2*self.logP[i][j])/(dGm*dGm)                       
            #Second derivative in both direction
            C = (self.logP[i+1][j+1] + self.logP[i-1][j-1]
                -self.logP[i-1][j+1] - self.logP[i+1][j-1])/(4*dGp*dGm)
            # Get the covariance matrix element 
            D2 = A*B-C*C
            # IF is too flat
            if not(D2 == 0 ): 
                self.cov_Gp = B/D2
                self.cov_Gm = A/D2
                self.cov_GpGm = C/D2    
            else:
                gp_width = (max(self.gp_axis) - min(self.gp_axis))/2 
                gm_width = (max(self.gm_axis) - min(self.gm_axis))/2 
                self.cov_Gp = gp_width*gp_width
                self.cov_Gm = gm_width*gm_width
                self.cov_GpGm = 0
                
            _debug('Parabola: A = %f'%A)
            _debug('Parabola: B = %f'%B)
            _debug('Parabola: C = %f'%C)
            _debug('Parabola: D2 = %f'%D2)
                
        elif method == 'mix':
            
            """
            Take the parabola, but take the integral for the variance if the 
            maximum is on the edge. 
            """
            _debug('Mix')
            # Take the maximum of the posterior for the best estimate
            # Use the logarithm of the posterior, to ease the calculation
            self.logP = -np.log(self.Ppost) # DO NOT take self.L, because we also need the prior
            # Get the indices of the minimum 
            shape = self.logP.shape
            self.ind = np.unravel_index(self.logP.argmin(), shape)
            i = self.ind[0]
            j = self.ind[1]
            
            self.Gp_guess = self.Gp_Axis[i][j]  # The mean is for if there are more than one max
            self.Gm_guess = self.Gm_Axis[i][j] 
            
            # If on the edge, get the error from the integral
            if (i==0) or (i==shape[0]-1) or (j==0) or (j == shape[1]-1):
                _debug('Readout ', self.R_tot, 'Method Integral')
                self.cov_Gp   = self.integral2D(self.gp_axis, self.gm_axis, self.Ppost*(self.Gp_Axis-self.Gp_guess)**2)
                self.cov_Gm   = self.integral2D(self.gp_axis, self.gm_axis, self.Ppost*(self.Gm_Axis-self.Gm_guess)**2)
                self.cov_GpGm = self.integral2D(self.gp_axis, self.gm_axis, self.Ppost*(self.Gm_Axis-self.Gm_guess)*(self.Gp_Axis-self.Gp_guess)) #Non-diagonal element of the cov matrix               
            else:
                _debug('Readout ', self.R_tot, 'Method Parabola')
                # Second derivative in the direction of gamma+
                dGp = self.Gp_Axis[i][j+1] - self.Gp_Axis[i][j]
                A = (self.logP[i][j+1]+self.logP[i][j-1]-2*self.logP[i][j])/(dGp*dGp) 
                # Second derivative in the direction of gamma-
                dGm = self.Gm_Axis[i+1][j+1] - self.Gm_Axis[i][j]
                B = (self.logP[i+1][j]+self.logP[i-1][j]-2*self.logP[i][j])/(dGm*dGm)                       
                #Second derivative in both direction
                C = (self.logP[i+1][j+1] + self.logP[i-1][j-1]
                    -self.logP[i-1][j+1] - self.logP[i+1][j-1])/(4*dGp*dGm)
                # Get the covariance matrix element 
                D2 = A*B-C*C
                self.cov_Gp = B/D2
                self.cov_Gm = A/D2
                self.cov_GpGm = C/D2  

        elif method == 'egde_is_uncertain':            
            """
            Take the parabola, but if the max is on the edge, the
            uncertainty is half the width of the prior. 
            """
            _debug('egde_is_uncertain')
            # Take the maximum of the posterior for the best estimate
            # Use the logarithm of the posterior, to ease the calculation
            self.logP = -np.log(self.Ppost) # DO NOT take self.L, because we also need the prior
            # Get the indices of the minimum 
            shape = self.logP.shape
            self.ind = np.unravel_index(self.logP.argmin(), shape)
            i = self.ind[0]
            j = self.ind[1]
            
            self.Gp_guess = self.Gp_Axis[i][j]  # The mean is for if there are more than one max
            self.Gm_guess = self.Gm_Axis[i][j] 
            
            if (i==0) or (i==shape[0]-1) or (j==0) or (j == shape[1]-1):
                gp_width = (max(self.gp_axis) - min(self.gp_axis))/2 
                gm_width = (max(self.gm_axis) - min(self.gm_axis))/2 
                self.cov_Gp = gp_width*gp_width
                self.cov_Gm = gm_width*gm_width
                self.cov_GpGm = 0
            else:
                _debug('Readout ', self.R_tot, 'Method Parabola')
                # Second derivative in the direction of gamma+
                dGp = self.Gp_Axis[i][j+1] - self.Gp_Axis[i][j]
                A = (self.logP[i][j+1]+self.logP[i][j-1]-2*self.logP[i][j])/(dGp*dGp) 
                # Second derivative in the direction of gamma-
                dGm = self.Gm_Axis[i+1][j+1] - self.Gm_Axis[i][j]
                B = (self.logP[i+1][j]+self.logP[i-1][j]-2*self.logP[i][j])/(dGm*dGm)                       
                #Second derivative in both direction
                C = (self.logP[i+1][j+1] + self.logP[i-1][j-1]
                    -self.logP[i-1][j+1] - self.logP[i+1][j-1])/(4*dGp*dGm)
                # Get the covariance matrix element 
                D2 = A*B-C*C
                self.cov_Gp = B/D2
                self.cov_Gm = A/D2
                self.cov_GpGm = C/D2  
                
        elif method == 'peakMax_varianceIntegral':            
            """
            For the best guess, take the max. 
            For the uncertainty, take the integral.
            
            Note that this should bug. See the notebook.
            """
            _debug('Mix')
            # Take the maximum of the posterior for the best estimate
            # Use the logarithm of the posterior, to ease the calculation
            self.logP = -np.log(self.Ppost) # DO NOT take self.L, because we also need the prior
            # Get the indices of the minimum 
            shape = self.logP.shape
            self.ind = np.unravel_index(self.logP.argmin(), shape)
            i = self.ind[0]
            j = self.ind[1]
            
            self.Gp_guess = self.Gp_Axis[i][j]  # The mean is for if there are more than one max
            self.Gm_guess = self.Gm_Axis[i][j] 
            
            self.cov_Gp   = self.integral2D(self.gp_axis, self.gm_axis, self.Ppost*(self.Gp_Axis-self.Gp_guess)**2)
            self.cov_Gm   = self.integral2D(self.gp_axis, self.gm_axis, self.Ppost*(self.Gm_Axis-self.Gm_guess)**2)
            self.cov_GpGm = self.integral2D(self.gp_axis, self.gm_axis, self.Ppost*(self.Gm_Axis-self.Gm_guess)*(self.Gp_Axis-self.Gp_guess)) #Non-diagonal element of the cov matrix               
            
        # Get the error from the covariant diagonal
        self.eGp_guess  = np.sqrt(self.cov_Gp)
        self.eGm_guess  = np.sqrt(self.cov_Gm)      

    def initialize(self, gp_axis, gm_axis, prior):
        """
        Initialize attributes and the protocol. 
        Prepare all the arrays and stuffs needed for running the iterations of
        the protocol. 
        
        gp_axis: 
            1D array of the axis for gamma+
        gm_axis: 
            1D array of the axis for gamma-
        prior: 
            2D array of the prior probability density for gamma+ and gamma-. 
            No need to be normalized. It is normalized in this function.  
        """     
        _debug('Bayes3Measure: initialize')
        
        #Define the axis over which we estimate the rates and the probability distribution
        self.gp_axis = gp_axis #1D axis for gamma+
        self.gm_axis = gm_axis #1D axis for gamma-
        self.NGp    = len(self.gp_axis)       #Number of discrete point along the gamma+ axis for the probability distributions.
        self.NGm    = len(self.gm_axis)       #Number of discrete point along the gamma- axis for the probability distributions. 
        #Meshgrid
        self.Gp_Axis, self.Gm_Axis = np.meshgrid(self.gp_axis, self.gm_axis)  
        #Note the bounds of the prior
        self.Gp_upperBound = np.max(self.gp_axis)
        self.Gp_lowerBound  = np.min(self.gp_axis)
        self.Gm_upperBound = np.max(self.gm_axis)
        self.Gm_lowerBound  = np.min(self.gm_axis)
        
        #Get the prior and normalize it
        self.prior = prior #Prior distribution
        
        # Initial the like-lihood. With now measurement for now.
        self.L = np.zeros(np.shape(self.Gp_Axis)) #This will be related to the logatirhtm of the like-lihood. It simplify a lot the calculation and reduce the number of calculation 
      
        # Initiate the posterior
        self.update_post()
        
        # Process the posterior for initiating the best guess and uncertainty
        self.process_post(method='integral')
        
        # Initiate  the best time to probe with the current knowledge
        self.determine_best_time_to_probe()
        
        #Check the normalization and guess
        _debug()
        _debug('Guess: Gp = %f kHz'%(self.Gp_guess*1e-3))
        _debug('Guess: Gm = %f kHz'%(self.Gm_guess*1e-3))
        _debug()
        
        #Initialise useful array

        
        self.compute_entropy = False #Define in simulate_V1
        self.entropy_s = [] # Will store the entropies computed



    def extract_rates(self, R):
        """
        Extract the rate from the measurements sor far. 
        
        R:
            Number of readout performed for each individual measure of the ms state.  
            (Useful for the expected error)
        """
        _debug('Bayes3Measure: extract_rates')
      
        # Apply Bayes 
        
        # Everything is multiplyied by R, because the like-lihood doens't 
        # distinguish the withd of the distribution with the mean. 
        # Get the expectation
        t_probe = self.t_probe
        exp_0 = self.f0(t_probe, self.Gp_Axis, self.Gm_Axis)*R
        exp_p = self.fp(t_probe, self.Gp_Axis, self.Gm_Axis)*R
        exp_m = self.fm(t_probe, self.Gp_Axis, self.Gm_Axis)*R
        self.L = self.get_likelihood_3measure(exp_0, exp_p, exp_m, 
                                              self.diff_p*R, self.diff_m*R)

        # Save the expecation if debug is on
        if _debug_enabled:
            self.exp_p = exp_p
            self.exp_m = exp_m
            self.exp_0 = exp_0
            
        # Update the posterior
        self.update_post()
        # Process the posterior for extracting informations 
        self.process_post()
        
    def determine_best_time_to_probe(self, method='betap'):
        """
        Determine the best time to probe with the current knowledge of the situation.
        """
        _debug('Bayes3Measure: determine_best_time_to_probe')
        # TODO really minimize the HitOn sensitivity or something like that instead. 
        if method == 'betap':
            #take 0.5/beta+
            Gp = self.Gp_guess
            Gm = self.Gm_guess
            G0 = np.sqrt(Gp*Gp + Gm*Gm - Gp*Gm)
            betap = Gp + Gm + G0
            self.t_probe = 0.5/betap
        
        elif method == 'expSensitivity':
            """
            Find the time to probe which minimize the expected sensitivity.
            We minimize the sum in quadrature of the sensitivites for gamma+ and gamma-
            """
            _debug('Probably time consuming ;D ')
        
            # Take the guess for the best time to be the gu 
            t_guess = self.best_time(method='betap')
            res = minimize(self.expected_sensitivity, [t_guess], method='Nelder-Mead')
            self.t_probe =  res.x[0] #Optimal tp 
    
    def get_t_probe(self):
        """
        Get t_probe
        """
        return self.t_probe
    
    def get_gp_axis(self):
        """
        Get gp_axi
        """
        return self.gp_axis
    
    def get_gm_axis(self):
        """
        Get gm_axi
        """
        return self.gm_axis
    
    def get_posterior(self):
        """
        Get it. 
        """
        return self.Ppost
    
    def run(self, R):
        """
        Perform one complete step of the protocol:
            Take measurements.
            Extract the results.
            Get the rate from the results.
            
        R:
            Number of readout to perform on each individual measure of the PC.
                        
        """                   
        _debug('\nBayes3Measure. Iteration', self.iter)
        
        # Take the measurement
        # This method is form the parent Protocol. It should update the results.
        self.measure_3PL(self.t_probe, R) 
        
        #Start the timer for  the processing time
        start_timeProcess = time.time()            
        # extract the rates
        self.extract_rates(R)
        
        # Note the processing time 
        self.t_process = time.time() - start_timeProcess  
                
        # Update the total elapsed time
        # This is redundant, but might help for defining the adaptive protocol. 
        self.t_tot_process = self.t_process 
        self.t_tot_pulseSequences = self.t_pulseSequences

        #Store the information 
        #First need to have knowledge about the posterior, if not updated yet
        self.process_post()         
        
        self.store_info()    
        # Compute entropy is wanted
        if self.compute_entropy:
            Z = -self.Ppost*np.log(self.Ppost)
            S = self.integral2D(self.gp_axis, self.gm_axis, Z)
            self.entropy_s.append(S)
        else:
            self.entropy_s.append(0)        
        
        #Check the guesses
        _debug('Guess: Gp = %f +- %f kHz'%(self.Gp_guess*1e-3, self.eGp_guess*1e-3))
        _debug('Guess: Gm = %f +- %f kHz'%(self.Gm_guess*1e-3, self.eGm_guess*1e-3))             
        

    def simulate_V1(self,t_probe, gp_axis, gm_axis, prior,
                    R=1e5, i_store=0, i_rediscretize=0, compute_entropy=False):
        """
        Simulate the protocole, version 1. 
        1. Initialize the protocole
        2. Run the iterations
        
        R: 
            Number of readout per iteration to take
        i_store: 
            numpy array of index of the iteration for which we want to 
            store the information
        i_rediscretize: 
            numpy array of index of the iteration for which we want to 
            rediscretize the domain. Must be contained in i_store.
        compute_entropy:
            If true, will compute the entropy of the posterior. 
        """
        
        #Initialize the simulation
        self.initialize(t_probe, gp_axis, gm_axis, prior)
        
        self.compute_entropy = compute_entropy # After initializae, to make it true
        
        #Run the iterations
        run_once = False # Note if the protocle as been ran once of not. 
        for i in i_store:
            self.iter = i
            R_cum = i*R # Number of readout to perform
            # Rediscretize
            if (np.sum(i == i_rediscretize) > 0) and run_once:
                self.rediscretization()  
            #Take a measure and update the guess for the rate.    
            self.run(R_cum)          
            run_once = True
 
                
    def integral2D(self, x,y, Z):
        """
        Redundant for now, just for not having to modify the code ;) 
        """
        return integral_2D(x,y,Z)
        
    def rediscretization(self, nb_std_from_mean=5):
        """
        Rediscretization of the domain (=gamma+ and gamma- axis'es) based on 
        the standard deviation of the distribution in both direction. 
        
        nb_std_from_mean:
            Number of standart deviation away from the mean for the boundary of the domain. 
            
        """
        _debug('Bayes3Measure: rediscretization' )  
        
        self.nbStdFromMean = nb_std_from_mean    

        # First need to have knowledge about the posterior,
        _debug('Warning. Re-process for rediscretization')
        self.update_post()
        self.process_post()          
        
        # Define the interpolator for L and post before redefining the axis
        f_inter_L    = interpolate.interp2d(self.gp_axis, self.gm_axis, self.L, kind='linear')
        # Define the new bounds
        delta_Gp = self.nbStdFromMean*np.sqrt(self.cov_Gp)
        delta_Gm = self.nbStdFromMean*np.sqrt(self.cov_Gm)
        # Also make sure that we don't have negative bounds !!
        # Or that the new bound are outside the prior !
        Gp_lowerBound = self.Gp_guess - delta_Gp
        if Gp_lowerBound < self.Gp_lowerBound:
            Gp_lowerBound = self.Gp_lowerBound
            
        Gp_upperBound = self.Gp_guess + delta_Gp
        if Gp_upperBound> self.Gp_upperBound:
            Gp_upperBound = self.Gp_upperBound
            
        Gm_lowerBound = self.Gm_guess - delta_Gm
        if Gm_lowerBound < self.Gm_lowerBound:
            Gm_lowerBound = self.Gm_lowerBound
            
        Gm_upperBound = self.Gm_guess + delta_Gm
        if Gm_upperBound> self.Gm_upperBound:
            Gm_upperBound = self.Gm_upperBound     
        
        #ReDefine the axis over which we estimate the rates and the probability distribution
        self.gp_axis = np.linspace(Gp_lowerBound, Gp_upperBound, self.NGp) 
        self.gm_axis = np.linspace(Gm_lowerBound, Gm_upperBound, self.NGm) 
        #Meshgrid
        self.Gp_Axis, self.Gm_Axis = np.meshgrid(self.gp_axis, self.gm_axis)
        #Interpolate the quantities 
        self.L = f_inter_L(self.gp_axis, self.gm_axis)
        
        #Get useful information for seeign how is going the rediscretization
        _debug('Bayes3Measure: rediscretization: delta_Gp = %f kHz'%(delta_Gp*1e-3) )
        _debug('Bayes3Measure: rediscretization: delta_Gm = %f kHz'%(delta_Gm*1e-3) )
        _debug('Bayes3Measure: rediscretization: Gp_lowerBound = %f kHz'%(Gp_lowerBound*1e-3) )
        _debug('Bayes3Measure: rediscretization: Gp_upperBound = %f kHz'%(Gp_upperBound*1e-3) )
        _debug('Bayes3Measure: rediscretization: Gm_lowerBound = %f kHz'%(Gm_lowerBound*1e-3) )
        _debug('Bayes3Measure: rediscretization: Gm_upperBound = %f kHz'%(Gm_upperBound*1e-3) )
        _debug('Bayes3Measure: rediscretization: np.sqrt(cov_Gp) = %f kHz'%(np.sqrt(self.cov_Gp)*1e-3) )
        _debug('Bayes3Measure: rediscretization: np.sqrt(cov_Gm) = %f kHz'%(np.sqrt(self.cov_Gm)*1e-3) )
        _debug()        



class ExpectedResult():
    """
    A class to get the expected result. 
    Get the expected uncertainty. 
    Get the expected correlation in the parameter. 
    Get the expected sensitivity. 
    
    This class aims to developpe a strong understanding of the Bayes protocol. 
    
    
    """
    def __init__(self, PL0, C):
        """
        PL0:
            Photoluminescence of the state ms=0
        C: constrast in PL for the state ms=+-
        """      
        _debug('Don’t wait for opportunity. Create it.')
        
        # Load some useful function
        self.PLms0  = experiment.analytic(PL0, C).PLms0
        self.PLmsP1 = experiment.analytic(PL0, C).PLmsP1
        self.PLmsM1 = experiment.analytic(PL0, C).PLmsM1
        
        self.diff_P  = experiment.analytic(PL0, C).diff_P
        self.diff_M  = experiment.analytic(PL0, C).diff_M    
         
        self.ediff_P = experiment.analytic(PL0, C).ediff_P
        self.ediff_M = experiment.analytic(PL0, C).ediff_M        
    
    def initialize(self, Gp, Gm, R=1e4):
        """
        Define the posterior and the domain, etc. 
        
        Gp, Gm: 
            Rates gamma+ gamma-         
        R: 
            number of readout performed. (Note that the sensitivity should 
            be independant of the number of readout when it is large enought
            to distinguish the states. It is included here for consistency of 
            the maths and to ease the code)        
        """
        self.Gp_true = Gp
        self.Gm_true = Gm
        self.R = R
        
        
        # Define the domain of integration
        #TODO Find a more intelligent way to define the domain, 
        #by considering the expected standard deviation based on the number of measurement ??? 
        # Fornow, just take the order of magnitude. 
        Gp_min = Gp /5  
        Gp_max = 5*Gp   
        Gm_min = Gm/5
        Gm_max = 5*Gm   
        #Define the axis for the prior pdf      
        #TODO verify is the granulation is good. Maybe not I the domain is overkill. 
        self.gp_axis = np.linspace(Gp_min, Gp_max, 200) 
        self.gm_axis = np.linspace(Gm_min, Gm_max, 200) 
        self.Gp_Axis, self.Gm_Axis = np.meshgrid(self.gp_axis, self.gm_axis)
        
    def model_3measurements(self,t_probe, t_ps_0, t_ps_pm, Gp, Gm, R=1e4, method='parabola'):
        """
        Return the expected uncertainty for gamma+ and gamma- if you are to 
        measure at time tp and tm over and over. 
        Assum a flat prior (for now). An upgrade of the function would be to 
        input also the prior. 
        
        t_probe:
            probing time
        t_ps_0: 
            time duration of the pulse sequence for the measurement of ms=0 NOT INCLUDING THE PROBING TIME
        t_ps_pm: 
            time duration of the pulse sequence for the measurement of ms=+-1 NOT INCLUDING THE PROBING TIME
            
        Gp, Gm: 
            Rates gamma+ gamma-         
        R: 
            number of readout performed per ms state. (Note that the sensitivity should 
            be independant of the number of readout when it is large enought
            to distinguish the states. It is included here for consistency of 
            the maths and to ease the code)     
        method:
            String defining which way to extract the mean, variance, correlation, etc. 
            
        """
        # Initialize the posterior and the domain. 
        self.initialize(Gp, Gm, R)
        
        # Measured difference
        diff_p = self.diff_P(t_probe, Gp, Gm)*R
        diff_m = self.diff_M(t_probe, Gp, Gm)*R
        
        exp_0 = self.PLms0 (t_probe, self.Gp_Axis, self.Gm_Axis)*R
        exp_p = self.PLmsP1(t_probe, self.Gp_Axis, self.Gm_Axis)*R
        exp_m = self.PLmsM1(t_probe, self.Gp_Axis, self.Gm_Axis)*R
        
        # Precompute arrays for simplification
        ZZZ = exp_p*exp_m +exp_0*(exp_p+exp_m)
        
        A = (exp_0 + exp_p + exp_m +2*(diff_p+diff_m) 
            + diff_p*diff_p/exp_p + diff_m*diff_m/exp_m )
        
        B = (exp_p*diff_m + exp_m*(3*exp_p+diff_p))**2       
        C = exp_0/(exp_p*exp_m*ZZZ)
        # THE like-lihood
        self.L = 0.5*(np.log(ZZZ) + A - B*C )

        # Extract information about the posterior
        self.process_post(method) # That will update the attributes
        
        # Get the sensitivity
        self.t_tot = R*(3*t_probe + t_ps_0 + 2*t_ps_pm) # Total time
        self.eta_Gp = self.eGp_guess*np.sqrt(self.t_tot)
        self.eta_Gm = self.eGm_guess*np.sqrt(self.t_tot)
    
        return (self.Gp_guess, self.Gm_guess, 
                self.eGp_guess, self.eGm_guess, self.cov_GpGm,
                self.eta_Gp, self.eta_Gm)  
        
    def model_6measurements(self,tp, tm, t_ps_0, t_ps_pm, Gp, Gm, R=1e4, method='parabola'):
        """
        Return the expected uncertainty for gamma+ and gamma- if you are to 
        measure at time tp and tm over and over. 
        Assum a flat prior (for now). An upgrade of the function would be to 
        input also the prior. 
        
        tp: 
            probing time at whicht the difference + is measured. 
        tm: 
            probing time at whicht the difference - is measured. 
        t_ps_0: 
            time duration of the pulse sequence for the measurement of ms=0 NOT INCLUDING THE PROBING TIME
        t_ps_pm: 
            time duration of the pulse sequence for the measurement of ms=+-1 NOT INCLUDING THE PROBING TIME
        Gp, Gm: 
            Rates gamma+ gamma-         
        R: 
            number of readout performed per ms state. (Note that the sensitivity should 
            be independant of the number of readout when it is large enought
            to distinguish the states. It is included here for consistency of 
            the maths and to ease the code)     
        method:
            String defining which way to extract the mean, variance, correlation, etc. 
            
        """
        # Initialize the posterior and the domain. 
        self.initialize(Gp, Gm, R)
              
        # Measured differences at tp
        diff_p = self.diff_P(tp, Gp, Gm)*R
        diff_m = self.diff_M(tp, Gp, Gm)*R
        
        exp_0 = self.PLms0 (tp, self.Gp_Axis, self.Gm_Axis)*R
        exp_p = self.PLmsP1(tp, self.Gp_Axis, self.Gm_Axis)*R
        exp_m = self.PLmsM1(tp, self.Gp_Axis, self.Gm_Axis)*R
        
        # Precompute arrays for simplification
        ZZZ = exp_p*exp_m +exp_0*(exp_p+exp_m)
        
        A = (exp_0 + exp_p + exp_m +2*(diff_p+diff_m) 
            + diff_p*diff_p/exp_p + diff_m*diff_m/exp_m )
        
        B = (exp_p*diff_m + exp_m*(3*exp_p+diff_p))**2       
        C = exp_0/(exp_p*exp_m*ZZZ)
        # THE like-lihood
        self.Lp = 0.5*(np.log(ZZZ) + A - B*C )
        
        
        # Measured differences at tm
        diff_p = self.diff_P(tm, Gp, Gm)*R
        diff_m = self.diff_M(tm, Gp, Gm)*R
        
        exp_0 = self.PLms0 (tm, self.Gp_Axis, self.Gm_Axis)*R
        exp_p = self.PLmsP1(tm, self.Gp_Axis, self.Gm_Axis)*R
        exp_m = self.PLmsM1(tm, self.Gp_Axis, self.Gm_Axis)*R
        
        # Precompute arrays for simplification
        ZZZ = exp_p*exp_m +exp_0*(exp_p+exp_m)
        
        A = (exp_0 + exp_p + exp_m +2*(diff_p+diff_m) 
            + diff_p*diff_p/exp_p + diff_m*diff_m/exp_m )
        
        B = (exp_p*diff_m + exp_m*(3*exp_p+diff_p))**2       
        C = exp_0/(exp_p*exp_m*ZZZ)
        # THE like-lihood
        self.Lm = 0.5*(np.log(ZZZ) + A - B*C )        
        
        # Total likelihood
        self.L = self.Lp + self.Lm
        
        # Extract information about the posterior
        self.process_post(method) # That will update the attributes
        
        # Get the sensitivity
        self.t_tot = R*( 3*tp + t_ps_0 + 2*t_ps_pm
                        +3*tm + t_ps_0 + 2*t_ps_pm) # Total time
        # Sensitivities
        self.eta_Gp = self.eGp_guess*np.sqrt(self.t_tot)
        self.eta_Gm = self.eGm_guess*np.sqrt(self.t_tot)
    
        return (self.Gp_guess, self.Gm_guess, 
                self.eGp_guess, self.eGm_guess, self.cov_GpGm,
                self.eta_Gp, self.eta_Gm)     
        
    def model_4measurements(self,tp, tm, t_ps_0, t_ps_pm, Gp, Gm, R=1e4, method='parabola'):
        """
        Return the expected uncertainty for gamma+ and gamma- if you are to 
        measure at time tp and tm over and over. 
        Assum a flat prior (for now). An upgrade of the function would be to 
        input also the prior. 
        
        tp: 
            probing time at whicht the difference + is measured. 
        tm: 
            probing time at whicht the difference - is measured. 
        t_ps_0: 
            time duration of the pulse sequence for the measurement of ms=0 NOT INCLUDING THE PROBING TIME
        t_ps_pm: 
            time duration of the pulse sequence for the measurement of ms=+-1 NOT INCLUDING THE PROBING TIME
        Gp, Gm: 
            Rates gamma+ gamma-         
        R: 
            number of readout performed per ms state. (Note that the sensitivity should 
            be independant of the number of readout when it is large enought
            to distinguish the states. It is included here for consistency of 
            the maths and to ease the code)     
        method:
            String defining which way to extract the mean, variance, correlation, etc. 
            
        """
        # Initialize the posterior and the domain. 
        self.initialize(Gp, Gm, R)
              
        # Measured difference
        diff_p = self.diff_P(tp, Gp, Gm)
        diff_m = self.diff_M(tm, Gp, Gm)
        
        # Defined the expected differences for each value of the rates
        diff_p_exp = self.diff_P(tp, self.Gp_Axis, self.Gm_Axis)
        diff_m_exp = self.diff_M(tm, self.Gp_Axis, self.Gm_Axis)
        
        # Defined the expected uncertainty in differences for each value of the rates
        ediff_p_exp = self.ediff_P(tp, self.Gp_Axis, self.Gm_Axis, R)
        ediff_m_exp = self.ediff_M(tm, self.Gp_Axis, self.Gm_Axis, R)
        
        # Get the Like-lihood
        L_p = (diff_p_exp - diff_p)*(diff_p_exp - diff_p)/(2*ediff_p_exp*ediff_p_exp)
        L_m = (diff_m_exp - diff_m)*(diff_m_exp - diff_m)/(2*ediff_m_exp*ediff_m_exp)
        self.L = L_p + L_m        
        
        # Extract information about the posterior
        self.process_post(method) # That will update the attributes
        
        # Get the sensitivity
        self.t_tot = 2*(t_ps_0 + t_ps_pm + tp + tm)* R #Total time
        self.eta_Gp = self.eGp_guess*np.sqrt(self.t_tot)
        self.eta_Gm = self.eGm_guess*np.sqrt(self.t_tot)
    
        return (self.Gp_guess, self.Gm_guess, 
                self.eGp_guess, self.eGm_guess, self.cov_GpGm,
                self.eta_Gp, self.eta_Gm)     

    def process_post(self, method='parabola'):
        """
        Normalize the posterior with the like-lihood. 
        Than extract all the information
        """
        
        # Normalize
        self.post = np.exp(-self.L)
        self.post /= integral_2D(self.gp_axis, self.gm_axis, self.post)  
        self.volume_post = integral_2D(self.gp_axis, self.gm_axis, self.post) # For verification
        _debug('ExpectedResult: Integral of the post: ',self.volume_post)    
            
        if method == 'integral':
            """
            Integrate the posterior with the corresponding weights for 
            extractiong quantities. 
            """
            # Extract the mean
            self.Gp_guess  = integral_2D(self.gp_axis, self.gm_axis, self.post*self.Gp_Axis)
            self.Gm_guess  = integral_2D(self.gp_axis, self.gm_axis, self.post*self.Gm_Axis)
            #Get the covariant matrix element
            self.cov_Gp   = integral_2D(self.gp_axis, self.gm_axis, self.post*(self.Gp_Axis-self.Gp_guess)**2)
            self.cov_Gm   = integral_2D(self.gp_axis, self.gm_axis, self.post*(self.Gm_Axis-self.Gm_guess)**2)
            self.cov_GpGm = integral_2D(self.gp_axis, self.gm_axis, self.post*(self.Gm_Axis-self.Gm_guess)*(self.Gp_Axis-self.Gp_guess)) #Non-diagonal element of the cov matrix    
        
        elif method == 'parabola':
            """
            Take second derivative around the maximum for estimating the 
            variance. 
            """
            # Take the maximum of the posterior for the best estimate
            self.ind = np.unravel_index(self.L.argmin(), self.L.shape)
            i = self.ind[0]
            j = self.ind[1]
            self.Gp_guess = self.Gp_Axis[i][j]  # The mean is for if there are more than one max
            self.Gm_guess = self.Gm_Axis[i][j] 
            
            # Second derivative in the direction of gamma+
            dGp = self.Gp_Axis[i][j+1] - self.Gp_Axis[i][j]
            A = (self.L[i][j+1]+self.L[i][j-1]-2*self.L[i][j])/(dGp*dGp) 
            # Second derivative in the direction of gamma-
            dGm = self.Gm_Axis[i+1][j+1] - self.Gm_Axis[i][j]
            B = (self.L[i+1][j]+self.L[i-1][j]-2*self.L[i][j])/(dGm*dGm)
                   
            #Second derivative in both direction
            C = (self.L[i+1][j+1] + self.L[i-1][j-1]
                -self.L[i-1][j+1] - self.L[i+1][j-1])/(4*dGp*dGm)
            # Get the covariance matrix element 
            D2 = A*B-C*C
            
            self.cov_Gp = B/D2
            if self.cov_Gp<0:
                self.cov_Gp   = integral_2D(self.gp_axis, self.gm_axis, self.post*(self.Gp_Axis-self.Gp_guess)**2)
            self.cov_Gm = A/D2
            if self.cov_Gm <0:
                self.cov_Gm   = integral_2D(self.gp_axis, self.gm_axis, self.post*(self.Gm_Axis-self.Gm_guess)**2)
            self.cov_GpGm = C/D2
        
        elif method == 'peakMeax_varianceInt':
            """
            For the best guess, take the max. 
            For the uncertainty, take the integral.
            
            """
            _debug('peakMeax_varianceInt')
            # Take the maximum of the posterior for the best estimate
            # Use the logarithm of the posterior, to ease the calculation
            self.logP = -np.log(self.post) # DO NOT take self.L, because we also need the prior
            # Get the indices of the minimum 
            shape = self.logP.shape
            self.ind = np.unravel_index(self.logP.argmin(), shape)
            i = self.ind[0]
            j = self.ind[1]
            
            self.Gp_guess = self.Gp_Axis[i][j]  # The mean is for if there are more than one max
            self.Gm_guess = self.Gm_Axis[i][j] 
            
            # Cannot simplify the integral, becasue the mean is not taken by the integral
            self.cov_Gp   = integral_2D(self.gp_axis, self.gm_axis, self.post*(self.Gp_Axis-self.Gp_guess)**2)
            self.cov_Gm   = integral_2D(self.gp_axis, self.gm_axis, self.post*(self.Gm_Axis-self.Gm_guess)**2)
            self.cov_GpGm = integral_2D(self.gp_axis, self.gm_axis, self.post*(self.Gm_Axis-self.Gm_guess)*(self.Gp_Axis-self.Gp_guess)) #Non-diagonal element of the cov matrix               
                          
        #Get the error from the covariant diagonal
        self.eGp_guess  = np.sqrt(self.cov_Gp)
        self.eGm_guess  = np.sqrt(self.cov_Gm)               
        
        return (self.Gp_guess, self.Gm_guess, 
                self.eGp_guess, self.eGm_guess, self.cov_GpGm) 
        
    def plot_prediction(self):
        """
        Plot the posterior and the prediction from the model. 
        """        
        post = self.post
        gp_axis = self.gp_axis
        gm_axis = self.gm_axis           
        Gp = self.Gp_guess
        Gm = self.Gm_guess   
        eGp = self.eGp_guess
        eGm = self.eGm_guess    
        corr = self.cov_GpGm/(eGp*eGm)
        plt.figure(tight_layout=True)
        plt.pcolor(gp_axis*1e-3,gm_axis*1e-3, post, cmap=plt.cm.jet)
        plt.colorbar(label="Probability density")
        plt.errorbar(Gp*1e-3, Gm*1e-3,xerr=eGp*1e-3,yerr=eGm*1e-3,
                     linestyle='', marker='.', color='k', label='Best $\Gamma$', markersize=20)
        plt.plot(self.Gp_true*1e-3, self.Gm_true*1e-3, 'xw', label='True $\Gamma$', markersize=20)
        plt.axis("equal")#Equate the axis for a better estimate of the relative error
        plt.xlabel('$\Gamma_+$ (kHz)')
        plt.ylabel('$\Gamma_-$ (kHz)')
        sci_R = "{:.1e}".format(self.R) #Put R in scientifique notation for clarity
        plt.title('Posterior'+
                  '\nVolume of post = %f'%self.volume_post+
                  '\n%s readouts in total'%sci_R+
                  '\ncorr = %f'%corr)
        plt.legend()          


class PlotBayes():
    """
    Plot stuff for bayes
    """

    def __init__(self, bayes_sim, Gp_true, Gm_true):
        """
        Extract the data. 
        bayes: 
            bayes object. 
        Gp_true, Gm_true:
            True rates 
        """
        #Load the bayes object
        self.bayes = bayes_sim
        self.Gp_true = Gp_true
        self.Gm_true = Gm_true
     
    def plot_post(self, logdomain=False):
        """
        Plot the posterior
        """
        post = self.bayes.Ppost
        gp_axis = self.bayes.gp_axis
        gm_axis = self.bayes.gm_axis           
        Gp = self.bayes.Gp_guess
        Gm = self.bayes.Gm_guess     
        eGp = self.bayes.eGp_guess
        eGm = self.bayes.eGm_guess       
        R_tot = self.bayes.R_tot
        corr = self.bayes.cov_GpGm/(eGp*eGm)
        sci_R = "{:.1e}".format(R_tot) #Put R in scientifique notation for clarity
        plt.figure(tight_layout=True)
        plt.pcolor(gp_axis*1e-3,gm_axis*1e-3, post, cmap=plt.cm.jet)
        plt.colorbar(label="Probability density")
        plt.errorbar(Gp*1e-3, Gm*1e-3,xerr=eGp*1e-3,yerr=eGm*1e-3,
                     linestyle='', marker='.', color='k', label='Best $\Gamma$', markersize=20)
        plt.plot(self.Gp_true*1e-3, self.Gm_true*1e-3, 'xw', label='True $\Gamma$', markersize=20)
        plt.axis("equal")#Equate the axis for a better estimate of the relative error
        plt.xlabel('$\Gamma_+$ (kHz)')
        plt.ylabel('$\Gamma_-$ (kHz)')
        plt.title('Posterior'+
                  '\n%d iterations'%(self.bayes.iter)+
                  '\n%s readouts in total'%sci_R+
                  '\ncorr = %f'%corr)
        plt.legend()  
        if logdomain:
            plt.xscale('log')
            plt.yscale('log')
        
    def plot_log_likelihood(self):
        """
        Plot the logarithm of the likelihood NOT NECESSARLY NORMALIZED
        """
        z = self.bayes.L
        gp_axis = self.bayes.gp_axis
        gm_axis = self.bayes.gm_axis           
        Gp = self.bayes.Gp_guess
        Gm = self.bayes.Gm_guess           
        R_tot = self.bayes.R_tot
        sci_R = "{:.1e}".format(R_tot) #Put R in scientifique notation for clarity
        plt.figure(tight_layout=True)
        plt.pcolor(gp_axis*1e-3,gm_axis*1e-3, z, cmap=plt.cm.jet)
        plt.colorbar(label="log Like-lihood (not normalized)")
        plt.plot(Gp*1e-3, Gm*1e-3,   'xk', label='Guess $\Gamma$', markersize=20)
        plt.plot(self.Gp_true*1e-3, self.Gm_true*1e-3, 'xw', label='True $\Gamma$', markersize=20)
        plt.axis("equal")#Equate the axis for a better estimate of the relative error
        plt.xlabel('$\Gamma_+$ (kHz)')
        plt.ylabel('$\Gamma_-$ (kHz)')
        plt.title('Reduced likelihood'+
                  '\n%d iterations'%(self.bayes.iter)+
                  '\n%s readouts in total'%sci_R)
        plt.legend()     


if __name__ == '__main__': 
    from traceback import print_exception as _p
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
    
    #Load information from the experiment
    exp = experiment.Experiment(model_functions, constants)
    Gp_true, Gm_true = exp.get_rates()
    
    #Define some conditions for the simulation
    # Times to probes
    t_probe = 0.4/(30*1e3)
    # Prior
    Gp_min = 0.1*1e3   #Minimum guess for gamma plus (Hz) 
    Gp_max = 200*1e3  #Maximun guess for gamma plus (Hz)        
    Gm_min = 0.01*1e3   #Minimum guess for gamma minus (Hz) 
    Gm_max = 150*1e3  #Maximun guess for gamma minus (Hz)  
    #Define the axis for the prior pdf      
    gp_axis = np.linspace(Gp_min, Gp_max, 150) 
    gm_axis = np.linspace(Gm_min, Gm_max, 210) 
    #Define the prior 
    prior = 1+np.zeros([len(gm_axis), len(gp_axis)])

    R = 7e2
    N_max = 50 # Maximum number of iteration to investigate
    N_store = N_max # Number of run that will be check
    i_store = np.geomspace(1,N_max-1, N_store, dtype=int) #logaritmic spacing
    

    self = Bayes3Measure(model_functions, constants)
    self.simulate_V1(t_probe, gp_axis, gm_axis, prior,R=R, 
                     i_store=i_store, i_rediscretize=i_store)
    
    from post_processing import PlotSingle
    ps = PlotSingle(self, Gp_true, Gm_true)
    ps.plot_rates('Bayes')
    ps.plot_sensitivities('Bayes')
    
    PlotBayes(self, Gp_true, Gm_true).plot_post()




