"""[summary]
Filename: predictor_new.py
Author: Yifan Meng <mailto:yifanm@mit.edu>
Based on version created by Kevin <mailto:kalyons@mit.edu> (kalyons11)
Description:

"""

import sys
import numpy as np
np.set_printoptions(threshold=np.nan)
from CityUtil.utils import *

log = logging.getLogger('__main__')
traffic_model = pickle.load(open(config.LINEAR_MODEL_FILENAME, 'rb'))
solar_model = pickle.load(open(config.SOLAR_MODEL_FILENAME, 'rb'))

def predict_traffic(input_city):
    traffic_features = input_city.get_traffic()
    traffic_output = traffic_model.predict([traffic_features])[0]
    return traffic_output

def predict_solar(input_city):
    solar_features = input_city.get_solar()
    solar_output = solar_model.predict([solar_features])[0]
    return solar_output
    