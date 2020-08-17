# -*- coding: utf-8 -*-
"""
Created on Wed Jul  8 07:57:17 2020

Example of how to load the saturation curve

@author: Childresslab
"""



import spinmob as sm


d = sm.data.load(text='Select saturation curve ;)')

# Check the ckeys
print(d.ckeys)

# Get the axis name
label_s = []
for key in d.ckeys:
    label_s.append(key)




# Plot them
import matplotlib.pyplot as plt

plt.figure(tight_layout=True)

plt.subplot(121)
plt.plot(d[0], d[2])
plt.xlabel(label_s[0])
plt.ylabel(label_s[2])
   
plt.subplot(122)
plt.plot(d[2], d[1])
plt.xlabel(label_s[2])
plt.ylabel(label_s[1])

plt.title('Saturation')