# -*- coding: utf-8 -*-
"""
Created on Tue Jul  7 09:06:40 2026

@author: sebas
"""

import numpy as np
from scipy.interpolate import interp1d


def interpola_extrapolar(y_labels, x_labels=[2011,2022], max_label=2024):
    
    
    # Known points (x must be monotonically increasing)
    x_known = np.array(x_labels)
    
    y_known = np.array(y_labels)
    # Vector of target points where you want to evaluate
    
    
    x_queries_interpolate = np.array(range(x_labels[0], x_labels[1]+1,1 ))
    
    # Interpolate all query points at once
    
    interpolated_values = np.round(np.interp(x_queries_interpolate, x_known, y_known))
    
    
    # extrapolate
    x_queries_extrapolate = np.array(range(x_labels[1]+1, max_label+1,1 ))
    
    linear_extrapolator = interp1d(x_known, y_known, kind='linear', fill_value='extrapolate')
    
    extrapolated_values = np.round(linear_extrapolator(x_queries_extrapolate),1)
    
    return [np.concatenate((x_queries_interpolate,x_queries_extrapolate )), 
            np.concatenate((interpolated_values, extrapolated_values))]


if __name__ == '__main__':
    
    
    hola = interpola_extrapolar([2000, 4000])
    
    print(hola)


    
    
        

    
    
    

