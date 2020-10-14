# -*- coding: utf-8 -*-
"""
Created on Fri Oct  9 12:35:01 2020

Goal: Developper the Bayes inferencer

@author: Childresslab
"""


import numpy as np
import traceback
_p = traceback.print_last #Very usefull command to use for getting the last-not-printed error


_debug_enabled     = False
def _debug(*a):
    if _debug_enabled: 
        s = []
        for x in a: s.append(str(x))
        print(', '.join(s))
 

       
def expected_ms0(PL0, C, t, gamma_p, gamma_m):
    """
    Return the expected count per readout when initializing ms=0 and
    reading ms=0. 
    
    PL0:
        (float) Count per readout of the state ms=0 at time equal0
    C:
        (float) Contrast in photoluminescence from the ms=+-1 state. 
        This is defined such that the photoluminescence coming from ms=+-1 
        is PL0*(1-C)
    t:
        (float) Time elapsed after the initialization of the states. 
    gamma_p:
        (float or grid of float): Rate gamma +
    gamma_m:
        (float or grid of float): Rate gamma -
        
    """
    _debug('expected_ms0')
    
    A = PL0*(1-C*2/3)
    
    gamma_0 = np.sqrt(gamma_p*gamma_p + gamma_m*gamma_m - gamma_p*gamma_m)
    beta_p = gamma_p + gamma_m + gamma_0
    beta_m = gamma_p + gamma_m - gamma_0        
    
    term1 = (2*gamma_0 + gamma_p + gamma_m)*np.exp(-beta_p*t)
    term2 = (2*gamma_0 - gamma_p - gamma_m)*np.exp(-beta_m*t)
    
    return A + (term1 + term2)*C*PL0/(6*gamma_0)

def expected_msp(PL0, C, t, gamma_p, gamma_m):
    """
    Return the expected count per readout when initializing ms=+1 and
    reading ms=0. 
    
    PL0:
        (float) Count per readout of the state ms=0 at time equal0
    C:
        (float) Contrast in photoluminescence from the ms=+-1 state. 
        This is defined such that the photoluminescence coming from ms=+-1 
        is PL0*(1-C)
    t:
        (float) Time elapsed after the initialization of the states. 
    gamma_p:
        (float or grid of float): Rate gamma +
    gamma_m:
        (float or grid of float): Rate gamma -
        
    """
    _debug('expected_msp')
    
    A = PL0*(1-C*2/3)
    
    gamma_0 = np.sqrt(gamma_p*gamma_p + gamma_m*gamma_m - gamma_p*gamma_m)
    beta_p = gamma_p + gamma_m + gamma_0
    beta_m = gamma_p + gamma_m - gamma_0        
    
    term1 = (gamma_0 + 2*gamma_p - gamma_m)*np.exp(-beta_p*t)
    term2 = (gamma_0 - 2*gamma_p + gamma_m)*np.exp(-beta_m*t)
    
    return A - (term1 + term2)*C*PL0/(6*gamma_0)    

def expected_msm(PL0, C, t, gamma_p, gamma_m):
    """
    Return the expected count per readout when initializing ms=-1 and
    reading ms=0. 
    
    PL0:
        (float) Count per readout of the state ms=0 at time equal0
    C:
        (float) Contrast in photoluminescence from the ms=+-1 state. 
        This is defined such that the photoluminescence coming from ms=+-1 
        is PL0*(1-C)
    t:
        (float) Time elapsed after the initialization of the states. 
    gamma_p:
        (float or grid of float): Rate gamma +
    gamma_m:
        (float or grid of float): Rate gamma -
        
    """
    _debug('expected_msm')
    
    A = PL0*(1-C*2/3)
    
    gamma_0 = np.sqrt(gamma_p*gamma_p + gamma_m*gamma_m - gamma_p*gamma_m)
    beta_p = gamma_p + gamma_m + gamma_0
    beta_m = gamma_p + gamma_m - gamma_0        
    
    term1 = (gamma_0 + 2*gamma_m - gamma_p)*np.exp(-beta_p*t)
    term2 = (gamma_0 - 2*gamma_m + gamma_p)*np.exp(-beta_m*t)
    
    return A - (term1 + term2)*C*PL0/(6*gamma_0)        


def expected_diffp(CPL0, t, gamma_p, gamma_m):
    """
    Return the expected difference between the counts per readout of an 
    initialization in ms=0 and ms=+1
    Note: Its count PER READOUT. 
    
    CPL0:
        (float) Product of the contrast and the expected count per readout of ms=0
        at time equal 0. 
    t:
        (float) Time elapsed after the initialization of the states. 
    gamma_p:
        (float or grid of float): Rate gamma +
    gamma_m:
        (float or grid of float): Rate gamma -
    """
    _debug('expected_diffp')
    
    gamma_0 = np.sqrt(gamma_p*gamma_p + gamma_m*gamma_m - gamma_p*gamma_m)
    beta_p = gamma_p + gamma_m + gamma_0
    beta_m = gamma_p + gamma_m - gamma_0
    
    term1 = (gamma_0+gamma_p)*np.exp(-beta_p*t)
    term2 = (gamma_0-gamma_p)*np.exp(-beta_m*t)
    
    return (term1 + term2)*CPL0/(2*gamma_0)

def expected_diffm(CPL0, t, gamma_p, gamma_m):
    """
    Return the expected difference between the counts per readout of an 
    initialization in ms=0 and ms=-1
    Note: Its count PER READOUT. 
    
    CPL0:
        (float) Product of the contrast and the expected count per readout of ms=0
        at time equal 0. 
    t:
        (float) Time elapsed after the initialization of the states. 
    gamma_p:
        (float or grid of float): Rate gamma +
    gamma_m:
        (float or grid of float): Rate gamma -
    """
    _debug('expected_diffm')
    
    gamma_0 = np.sqrt(gamma_p*gamma_p + gamma_m*gamma_m - gamma_p*gamma_m)
    beta_p = gamma_p + gamma_m + gamma_0
    beta_m = gamma_p + gamma_m - gamma_0
    
    term1 = (gamma_0+gamma_m)*np.exp(-beta_p*t)
    term2 = (gamma_0-gamma_m)*np.exp(-beta_m*t)
    
    return (term1 + term2)*CPL0/(2*gamma_0)    

def expected_diffp_width(N0, Np, PL0, C, t, gamma_p, gamma_m):
    """
    Return the expected width in the distribution of the difference +

    N0:
        (float) Total number of readout performed on ms=0
    Np:
        (float) Total number of readout performed on ms=+1
    PL0:
        (float) Count per readout of the state ms=0 at time equal0
    C:
        (float) Contrast in photoluminescence from the ms=+-1 state. 
        This is defined such that the photoluminescence coming from ms=+-1 
        is PL0*(1-C)
    t:
        (float) Time elapsed after the initialization of the states. 
    gamma_p:
        (float or grid of float): Rate gamma +
    gamma_m:
        (float or grid of float): Rate gamma -
        
    """
    _debug('Bayes: expected_diffp_width')
    
    PL0 = expected_ms0(PL0, C, t, gamma_p, gamma_m)
    PLp = expected_msp(PL0, C, t, gamma_p, gamma_m)
    
    return np.sqrt(PL0/N0 + PLp/Np)

def expected_diffm_width(N0, Nm, PL0, C, t, gamma_p, gamma_m):
    """
    Return the expected width in the distribution of the difference -

    N0:
        (float) Total number of readout performed on ms=0
    Nm:
        (float) Total number of readout performed on ms=-1
    PL0:
        (float) Count per readout of the state ms=0 at time equal0
    C:
        (float) Contrast in photoluminescence from the ms=+-1 state. 
        This is defined such that the photoluminescence coming from ms=+-1 
        is PL0*(1-C)
    t:
        (float) Time elapsed after the initialization of the states. 
    gamma_p:
        (float or grid of float): Rate gamma +
    gamma_m:
        (float or grid of float): Rate gamma -
        
    """
    _debug('Bayes: expected_diffm_width')
    
    PL0 = expected_ms0(PL0, C, t, gamma_p, gamma_m)
    PLm = expected_msm(PL0, C, t, gamma_p, gamma_m)
    
    return np.sqrt(PL0/N0 + PLm/Nm)

def integral_2D(x,y, Z):
    """
    Integrate in 2 dimension Z. 
    Z is the 2D array to integrate. 
    x and y are both 1D array used to define the axis of Z
    """
    _debug('integral2D')
    
    firstInt = np.trapz(Z, x=x, axis=1) #First integrate along the first axis
    return     np.trapz(firstInt, x=y) #Integrate over the remaining axis

class Bayes():
    """
    Bayes inference for infering the rates, based on the measurement of the
    difference in mean count per readout between the states. 
        
    """

    def __init__(self):
        """
            
        """
        _debug('Bayes: __init__')
        _debug('Your limitation-it’s only your imagination.')
        
    
    def initiate(self, mesh_prior, mesh_gp, mesh_gm):
        """
        Initiate the attributes. 
        Especially, it initiate the like-lihood. 

        mesh_prior:
            Meshgrid of the prior
        mesh_gp:
            Meshgrid of the rate gamma+
        mesh_gm:
            Meshgrid of the rate gamma-
        Note:
            The size of each meshgrids should be the exact same. 
        """
        
        # Set the attributes
        self.mesh_prior = mesh_prior          
        self.mesh_gp = mesh_gp
        self.mesh_gm = mesh_gm

        # Initiate the like-lihood and the posterior
        # We are using the logarithm of the like-lihood, for a better numerical
        # handling. 
        self.ln_Likelihood = 0*mesh_prior # The log of 1 ir zero. 
        # Update the posterior
        self.post = np.exp(self.ln_Likelihood)*self.mesh_prior
        # Normalize it
        self.post /= integral_2D(self.mesh_gp[0], 
                                 np.transpose(self.mesh_gm)[0], 
                                 self.post) #Normalize      
        
    def set_prior(self, mesh_prior):
        """
        Set the prior pdf. 
        
        mesh_prior:
            Meshgrid of the prior
        """
        _debug('Bayes: set_prior')
        
        self.mesh_prior = mesh_prior
        
        
    def set_domain(self, mesh_gp, mesh_gm):
        """
        Set the gamma+ and gamma- axis. 
        Maybe also PL0 and C ?
        
        mesh_gp:
            Meshgrid of the rate gamma+
        mesh_gm:
            Meshgrid of the rate gamma-
            
        Note:
            The size of each meshgrid should be the exact same. 
        """
        _debug('Bayes: set_domain')
        
        self.mesh_gp = mesh_gp
        self.mesh_gm = mesh_gm
        
    def update_post(self):
        """
        Update the posterior pdf, according to the current total like-lihood
        and prior. 
        """
        _debug('Bayes: update_post')
        
        # Update the posterior
        self.post = np.exp(self.ln_Likelihood)*self.mesh_prior
        # Normalize it
        self.post /= integral_2D(self.mesh_gp[0], 
                                 np.transpose(self.mesh_gm)[0], 
                                 self.post) #Normalize     
        
    def give_measurement_diffp(self, measurement, PL0, C, t, N0, Np):
        """
        Feed the algorithm with a measurement of the difference +.
        It gonna update the posterior accordingly. 
        
        measurement:
            (float) Value of the measured difference in the mean count per 
            readout.
        PL0:
            (float) Count per readout of the state ms=0 at time equal0
        C:
            (float) Contrast in photoluminescence from the ms=+-1 state. 
            This is defined such that the photoluminescence coming from ms=+-1 
            is PL0*(1-C)
        t:
            (float) Time probed for the measurement (in sec)
        N0:
            Number of readout of the ms=0 state. 
        Np:
            Number of readout of the ms=+ state. 

            
        """
        _debug('Bayes: give_measurement_diffp')
        
        # Update the attributes
        self.measured_diffp = measurement
        self.N0  = N0
        self.Np  = Np
        self.t   = t
        self.PL0 = PL0
        self.C   = C
        
        # Update the posterior
        # Compute the likelihhod
        # Get the meshgrid of the expected value, for each possible gammas
        self.mesh_z0 = expected_diffp(C*PL0, t, self.mesh_gp, self.mesh_gm)
        # Get the meshgrid of the expected widt in the distribution, for each possible gammas
        self.mesh_sigma_z0 = expected_diffp_width(N0, Np, PL0, C, t, 
                                       self.mesh_gp, self.mesh_gm)
        # Get the measurement, which is NOT a meshgrid
        self.z = measurement
        # We update the logarithm of the like-lihood (this ease the numeric calculation)
        ln1 = -(self.z-self.mesh_z0)**2/(2*self.mesh_sigma_z0*self.mesh_sigma_z0)
        ln2 = -np.log(self.mesh_sigma_z0)
        self.ln_Likelihood += ln1 + ln2
        
        self.update_post()
    
        
    def give_measurement_diffm(self, measurement, PL0, C, t, N0, Nm):
        """
        Feed the algorithm with a measurement of the difference -.
        It gonna update the posterior accordingly. 
        
        measurement:
            (float) Value of the measured difference in the mean count per 
            readout.
        PL0:
            (float) Count per readout of the state ms=0 at time equal0
        C:
            (float) Contrast in photoluminescence from the ms=+-1 state. 
            This is defined such that the photoluminescence coming from ms=+-1 
            is PL0*(1-C)
        t:
            (float) Time probed for the measurement (in sec)
        N0:
            Number of readout of the ms=0 state. 
        Nm:
            Number of readout of the ms=- state. 

            
        """
        _debug('Bayes: give_measurement_diffm')
        
        # Update the attributes
        self.measured_diffm = measurement
        self.N0  = N0
        self.Nm  = Nm
        self.t   = t
        self.PL0 = PL0
        self.C   = C
        
        # Update the posterior
        # Compute the likelihhod
        # Get the meshgrid of the expected value, for each possible gammas
        self.mesh_z0 = expected_diffm(C*PL0, t, self.mesh_gp, self.mesh_gm)
        # Get the meshgrid of the expected widt in the distribution, for each possible gammas
        self.mesh_sigma_z0 = expected_diffm_width(N0, Nm, PL0, C, t, 
                                       self.mesh_gp, self.mesh_gm)
        # Get the measurement, which is NOT a meshgrid
        self.z = measurement
        # We update the logarithm of the like-lihood (this ease the numeric calculation)
        ln1 = -(self.z-self.mesh_z0)**2/(2*self.mesh_sigma_z0*self.mesh_sigma_z0)
        ln2 = -np.log(self.mesh_sigma_z0)
        self.ln_Likelihood += ln1 + ln2
        
        # Update the posterior
        self.update_post()              
        
        
if __name__=="__main__":
    _debug_enabled = True
    
    # Check is the equations for the expetation work    
#    gp  = 35*1e3
#    gm  = 10*1e3
#    PL0 = 0.04
#    C   = 0.2
#    ts  = np.linspace(0, 4/gm, 100)
#    
#    PL0s =  expected_ms0(PL0, C, ts, gp, gm)
#    PLps =  expected_msp(PL0, C, ts, gp, gm)
#    PLms =  expected_msm(PL0, C, ts, gp, gm)
#    
#    diffps = PL0s - PLps
#    diffms = PL0s - PLms
#    
#    import matplotlib.pyplot as plt
#    plt.figure()
#    plt.plot(ts, PL0s, label="ms0")
#    plt.plot(ts, PLps, label="ms+")
#    plt.plot(ts, PLms, label="ms-")
#    plt.legend()
#    plt.xlabel('Time (s)')
#    plt.ylabel('Mean count per readout')
#    # Check if the equation for the difference matche the difference between the functions
#    plt.figure()
#    plt.plot(ts, diffps-(PL0s-PLps), label="Difference between the +s")
#    plt.plot(ts, (diffms-(PL0s-PLms))*2, label="Difference between the -s time2")
#    plt.legend()
#    plt.xlabel('Time (s)')
    
    
    # Test the Bayes class with a measurement of the difference plus
#    # Define the grid for th rates
#    Gp_min = 0.1*1e3   #Minimum guess for gamma plus (Hz) 
#    Gp_max = 35*1e3  #Maximun guess for gamma plus (Hz)        
#    Gm_min = 0.01*1e3   #Minimum guess for gamma minus (Hz) 
#    Gm_max = 50*1e3  #Maximun guess for gamma minus (Hz)  
#    #Define the domain      
#    gp_axis = np.linspace(Gp_min, Gp_max, 203) 
#    gm_axis = np.linspace(Gm_min, Gm_max, 173) 
#    mesh_gp, mesh_gm = np.meshgrid(gp_axis, gm_axis)
#    #Define the prior 
#    prior = 1+np.zeros([len(gm_axis), len(gp_axis)])
#    # Initiate the algorithm
#    self = Bayes()
#    self.initiate(prior, mesh_gp, mesh_gm)
#    # Feed a measurement
#    # Create a fake measurement
#    N = 30000
#    C   = 0.2
#    PL0 = 0.04
#    gp_exp = 15*1e3
#    gm_exp = 10*1e3
#    t_probe  = 0.5/gp_exp
#    x0 = expected_ms0(PL0, C, t_probe, gp_exp, gm_exp)
#    xp = expected_msp(PL0, C, t_probe, gp_exp, gm_exp)
#    # Add noise
#    C0 = np.random.poisson(x0*N)/N
#    Cp = np.random.poisson(xp*N)/N
#    measure = C0 - Cp
#    print('x0, C0 :', x0, C0)
#    print('xp, Cp :', xp, Cp)
#    print('Expected diff: ', x0-xp)
#    print('Measured diff: ', measure)
#    print('1/t_probe = ', 1e-3/t_probe, ' kHz')
#    self.give_measurement_diffp(measure, PL0, C, t_probe, N, N)
#    
#    # Look at the result
#    import matplotlib.pyplot as plt
#    plt.figure(tight_layout=True)
#    plt.pcolor(gp_axis*1e-3, gm_axis*1e-3, self.post,
#               cmap=plt.cm.jet, vmin=0)
#    plt.colorbar(label="Probability density")
#    plt.axis("equal")#Equate the axis for a better estimate of the relative error
#    plt.xlabel('$\Gamma_+$ (kHz)')
#    plt.ylabel('$\Gamma_-$ (kHz)')
#    plt.title('Posterior') 
    

#    # Test the Bayes class with a measurement of the difference minus
#    # Define the grid for th rates
#    Gp_min = 0.001*1e3   #Minimum guess for gamma plus (Hz) 
#    Gp_max = 35*1e3  #Maximun guess for gamma plus (Hz)        
#    Gm_min = 0.001*1e3   #Minimum guess for gamma minus (Hz) 
#    Gm_max = 10*1e3  #Maximun guess for gamma minus (Hz)  
#    #Define the domain      
#    gp_axis = np.linspace(Gp_min, Gp_max, 203) 
#    gm_axis = np.linspace(Gm_min, Gm_max, 301) 
#    mesh_gp, mesh_gm = np.meshgrid(gp_axis, gm_axis)
#    #Define the prior 
#    prior = 1+np.zeros([len(gm_axis), len(gp_axis)])
#    # Initiate the algorithm
#    self = Bayes()
#    self.initiate(prior, mesh_gp, mesh_gm)
#    # Feed a measurement
#    # Create a fake measurement
#    N = 30000
#    C   = 0.2
#    PL0 = 0.04
#    gp_exp = 15*1e3
#    gm_exp = 1*1e3
#    t_probe  = 0.5/gm_exp 
#    x0 = expected_ms0(PL0, C, t_probe, gp_exp, gm_exp)
#    xm = expected_msm(PL0, C, t_probe, gp_exp, gm_exp)
#    # Add noise
#    C0 = np.random.poisson(x0*N)/N
#    Cm = np.random.poisson(xm*N)/N
#    measure = C0 - Cm
#    print('x0, C0 :', x0, C0)
#    print('xm, Cp :', xm, Cm)
#    print('Expected diff: ', x0-xm)
#    print('Measured diff: ', measure)
#    print('1/t_probe = ', 1e-3/t_probe, ' kHz')
#    self.give_measurement_diffm(measure, PL0, C, t_probe, N, N)
#    
#    # Look at the result
#    import matplotlib.pyplot as plt
#    plt.figure(tight_layout=True)
#    plt.pcolor(gp_axis*1e-3, gm_axis*1e-3, self.post,
#               cmap=plt.cm.jet, vmin=0)
#    plt.colorbar(label="Probability density")
#    plt.axis("equal")#Equate the axis for a better estimate of the relative error
#    plt.xlabel('$\Gamma_+$ (kHz)')
#    plt.ylabel('$\Gamma_-$ (kHz)')
#    plt.title('Posterior') 
    
    
    
    # Test the Bayes class with a measurement of thetwo type of difference 
    # Define the grid for th rates
    Gp_min = 0.001*1e3   #Minimum guess for gamma plus (Hz) 
    Gp_max = 107*1e3  #Maximun guess for gamma plus (Hz)        
    Gm_min = 0.001*1e3   #Minimum guess for gamma minus (Hz) 
    Gm_max = 106*1e3  #Maximun guess for gamma minus (Hz)  
    #Define the domain      
    gp_axis = np.linspace(Gp_min, Gp_max, 203) 
    gm_axis = np.linspace(Gm_min, Gm_max, 301) 
    mesh_gp, mesh_gm = np.meshgrid(gp_axis, gm_axis)
    #Define the prior 
    prior = 1+np.zeros([len(gm_axis), len(gp_axis)])
    # Initiate the algorithm
    self = Bayes()
    self.initiate(prior, mesh_gp, mesh_gm)
    # Feed a measurement
    # Create a fake measurement
    N = 30000
    C   = 0.2
    PL0 = 0.04
    gp_exp = 35*1e3
    gm_exp = 2*1e3
    t_probe  = 0.1/gm_exp 
    
    # Measure the difference plus
    x0 = expected_ms0(PL0, C, t_probe, gp_exp, gm_exp)
    xp = expected_msp(PL0, C, t_probe, gp_exp, gm_exp)
    # Add noise
    C0 = np.random.poisson(x0*N)/N
    Cp = np.random.poisson(xp*N)/N
    measure = C0 - Cp
    print('x0, C0 :', x0, C0)
    print('xp, Cp :', xp, Cp)
    print('Expected diff: ', x0-xp)
    print('Measured diff: ', measure)
    print('1/t_probe = ', 1e-3/t_probe, ' kHz')
    self.give_measurement_diffp(measure, PL0, C, t_probe, N, N)

    
    # Measure the difference minus
    x0 = expected_ms0(PL0, C, t_probe, gp_exp, gm_exp)
    xm = expected_msm(PL0, C, t_probe, gp_exp, gm_exp)
    # Add noise
    C0 = np.random.poisson(x0*N)/N
    Cm = np.random.poisson(xm*N)/N
    measure = C0 - Cm
    print('x0, C0 :', x0, C0)
    print('xm, Cp :', xm, Cm)
    print('Expected diff: ', x0-xm)
    print('Measured diff: ', measure)
    print('1/t_probe = ', 1e-3/t_probe, ' kHz')
    self.give_measurement_diffm(measure, PL0, C, t_probe, N, N)
    
    # Look at the result
    import matplotlib.pyplot as plt
    plt.figure(tight_layout=True)
    plt.pcolor(gp_axis*1e-3, gm_axis*1e-3, self.post,
               cmap=plt.cm.jet, vmin=0)
    plt.colorbar(label="Probability density")
    plt.axis("equal")#Equate the axis for a better estimate of the relative error
    plt.xlabel('$\Gamma_+$ (kHz)')
    plt.ylabel('$\Gamma_-$ (kHz)')
    plt.title('Posterior')             
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        


