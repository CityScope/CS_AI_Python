import sys
import logging
log = logging.getLogger('__main__')
# INIT
if len(sys.argv) < 2:
    log.error("Proj name argv missing")
    log.error("Usage: python server_new.py proj_name")
    sys.exit(-1)
import time
import copy
import atexit
sys.path.extend(['..'])
import CityUtil.config as config
from CityUtil.cityio_http import *
from CityUtil.utils import *
from CityUtil.city_class import *
import CityPrediction.predictor_new as ML
import CityMAItrix.strategies.strategies_new as Strategy
from CityMAItrix.objective_new import objective

proj_name = sys.argv[1]
if len(sys.argv)>=3:
    if sys.argv[2] == "1":
        config.SAVE_TABLES = True
    elif sys.argv[2] == "0":
        config.SAVE_TABLES = False
old_input_city = None
old_output_city = None

def CompareInputCitys(old_city, new_city):
    if (old_city.cells == new_city.cells and 
        old_city.density == new_city.density and
        old_city.dock_id == new_city.dock_id):
        return True
    return False

def ComputeOutputCity(input_city):
    output_city = OutputCity(input_city)
    # Traffic/solar predictor
    output_city.calc_density()
    output_city.set_traffic(ML.predict_traffic(input_city))
    output_city.set_solar(ML.predict_solar(input_city))
    output_city.calc_density()
    output_city.calc_diversity()
    output_city.calc_energy()
    metricsScores = Strategy.scores(output_city)
    output_city.set_metrics(metricsScores[1])
    return output_city

def UpdateOutputCity(old_output, new_input):
    new_output = copy.deepcopy(old_output)
    new_output.heatmap = new_input.heatmap
    new_output.toggle = new_input.toggle
    new_output.input_ts = new_input.client_ts
    return new_output

CityIO = City_HTTP(proj_name)
# WHILE LOOP
while True:
    input_city = CityIO.get_table()
    # timestamp = str(int(time.time()))
    # log.info(input_city)
    if input_city is not None:
        if old_input_city is not None:
            if not old_input_city.equals(input_city):
                if CompareInputCitys(old_input_city, input_city):
                    log.info("[SERVER] Not same - same city")
                    output_city = UpdateOutputCity(old_output_city, input_city)
                    output_city.set_ts()
                    CityIO.post_table(output_city.to_json())
                    old_input_city = copy.deepcopy(input_city)
                    old_output_city = output_city
                else:
                    log.info("[SERVER] Not same - different city")
                    output_city = ComputeOutputCity(input_city)
                    output_city.set_ts()
                    CityIO.post_table(output_city.to_json())
                    old_input_city = copy.deepcopy(input_city)
                    old_output_city = output_city
            # else:
                # log.info("[SERVER] SAME")
                # log.info(id(old_input_city))
                # log.info(id(input_city))
        else:
            log.info("[SERVER] NO Previous City")
            output_city = ComputeOutputCity(input_city)
            # ai_city, move, ai_metrics_list = Strategy.search(ml_city)
            output_city.set_ts()
            CityIO.post_table(output_city.to_json())
            old_input_city = copy.deepcopy(input_city)
            old_output_city = output_city

    time.sleep(0.5)
