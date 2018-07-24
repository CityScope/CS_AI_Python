import sys
import logging
import time
import atexit
sys.path.extend(['../global/', '../CityPrediction/', '../CityMAItrix/'])
import config
from utils import *
import cityio_http
import predictor_new as ML
from strategies import strategies_new as Strategy
from objective_new import objective
from city_class import *

log = logging.getLogger('__main__')
# INIT
if len(sys.argv) < 2:
    log.error("Proj name argv missing")
    log.error("Usage: python server_new.py proj_name")
    sys.exit(-1)
proj_name = sys.argv[1]
previous_city = None

CityIO = cityio_http.City_HTTP(proj_name)
# WHILE LOOP
while True:
    input_city = CityIO.get_table()
    # timestamp = str(int(time.time()))
    # log.info(input_city)
    if input_city is not None:
        if previous_city is not None:
            if not previous_city == input_city:
                log.info("[SERVER] Not same")
                previous_city = input_city
            # elif input_city.toggle1 != previous_city.toggle1:
            #     log.info("[SERVER] New toggle")
            else:
                log.info("[SERVER] SAME")
        else:
            previous_city = input_city
            output_city = OutputCity(input_city)
            # Traffic/solar predictor
            output_city.calc_density()
            output_city.set_traffic(ML.predict_traffic(input_city))
            output_city.set_solar(ML.predict_solar(input_city))
            output_city.calc_density()
            output_city.calc_diversity()
            output_city.calc_energy()
            metricsScores = Strategy.scores(output_city)
            # log.info(metricsScores[1])
            output_city.set_metrics(metricsScores[1])
            # log.info(output_city.to_json())
            # ml_city.score = mlCityScores[0]
            # ai_city, move, ai_metrics_list = Strategy.search(ml_city)
            output_city.set_ts()
            CityIO.post_table(output_city.to_json())
            log.info("[SERVER] NO Previous City")

    time.sleep(0.5)
