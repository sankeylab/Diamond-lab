# -*- coding: utf-8 -*-
"""
Created on Mon Aug 17 16:34:14 2020

@author: Childresslab
"""

#        self.treeDic_settings.add_parameter('Rate_+_min', 0.01, 
#                                            type='float', step=0.1, 
#                                            bounds=[0,None], suffix=' Hz',
#                                            tip='Guess for the minimum value of the rate gamma+') 
#        self.treeDic_settings.add_parameter('Rate_+_max', 150*1e3, 
#                                            type='float', step=0.1, 
#                                            bounds=[0,None], suffix=' Hz',
#                                            tip='Guess for the maximum value of the rate gamma+') 
#        self.treeDic_settings.add_parameter('Size_rate_+_axis', 150, 
#                                            type='int', step=10, 
#                                            bounds=[0,None],
#                                            tip='Number of points along the gamma+ axis for the pdf') 
#        self.treeDic_settings.add_parameter('Rate_-_min', 0.01, 
#                                            type='float', step=0.1, 
#                                            bounds=[0,None], suffix=' Hz',
#                                            tip='Guess for the minimum value of the rate gamma-')         
#        self.treeDic_settings.add_parameter('Rate_-_max', 150*1e3, 
#                                            type='float', step=0.1, 
#                                            bounds=[0,None], suffix=' Hz',
#                                            tip='Guess for the maximum value of the rate gamma-')
#        self.treeDic_settings.add_parameter('Size_rate_-_axis', 150, 
#                                            type='int', step=10, 
#                                            bounds=[0,None],
#                                            tip='Number of points along the gamma- axis for the pdf') 
#        self.list_prior_types = ['Flat', 'Gaussian']
#        self.treeDic_settings.add_parameter('Prior_type', self.list_prior_types, 
#                                            tip='Which prior to use. Based on the bounds given for the rates.')  