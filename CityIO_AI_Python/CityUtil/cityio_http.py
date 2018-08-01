# importing the requests library
import os
import sys
import json
import time
import asyncio
import logging
import pathlib
import requests
import CityUtil.config as config
from CityUtil.city_class import *

log = logging.getLogger('__main__')

class City_HTTP():

    def __init__(self, proj_name):
        self.city = None
        self.URL_get = "https://cityio.media.mit.edu/api/table/" + proj_name + "_in"
        self.URL_post = "https://cityio.media.mit.edu/api/table/update/" + proj_name + "_out"
        self.PARAMS = {}
        self.HEADERS = {'Connection': 'close'}
        self.prev_text = ""
        self.prev_json = {}
        log.info("[City_HTTP] Init")

    def get_table(self):
        # log.info("[City_HTTP] Get table")
        r = requests.get(url = self.URL_get, headers = self.HEADERS)
        
        # Check if r is a valid response
        try:
            r.raise_for_status()
        except Exception as e:
            log.exception("[City_HTTP] GET: " + e)
            return None
        # Convert to text and json version for future use
        curr_text = r.text      # <class 'str'>
        curr_json = r.json()    # <class 'dict'>
        # Check if response is a valid json
        if not self.is_json(curr_text):
            log.exception("[City_HTTP] HTTP response is not valid JSON")
            return None
        # Check if r is a new json
        if not self.equal_dicts(curr_json, self.prev_json, {'meta'}):
            # print (curr_text)
            if config.SAVE_TABLES:
                asyncio.set_event_loop(asyncio.new_event_loop())
                loop = asyncio.get_event_loop()
                loop.run_until_complete(self.write_dict(curr_text))
                loop.close()
            # self.write_dict(curr_text)
            self.prev_text = curr_text
            self.prev_json = curr_json
            log.info("[City_HTTP] <GET> New data")
            if self.city is None:
                self.city = InputCity(curr_text)
            else:
                self.city.json_update(curr_text)
            return self.city
        return self.city

    def post_table(self, data):
        # log.info(json.dumps(data))
        json_obj = json.loads(data)
        # obj_wrap = {"objects": data}
        # with open("../jsonExamples/fake_output.json", 'r') as f:
        #     fake_output = json.load(f)
        # fake_url = "https://cityio.media.mit.edu/api/table/update/cityiotest_out"
        r = requests.post(url = self.URL_post, json = json_obj)
        # r = requests.post(url = self.URL_post, json = obj_wrap)
        # r = requests.post(url = fake_url, json = fake_output)
        log.info("[City_HTTP] <POST> Prediction sent to CityIO")
        # log.info(r)
        # Check if r is a valid response
        try:
            r.raise_for_status()
        except Exception as e:
            log.exception("[City_HTTP] POST: " + e)
            return None
        # self.sendto(json_message.encode(), (self.send_ip, self.send_port))

    # https://stackoverflow.com/questions/11294535/verify-if-a-string-is-json-in-python
    def is_json(self, myjson):
        try:
            self.json_object = json.loads(myjson)
        except Exception as e:
            log.exception("[City_HTTP] " + e)
            return False
        return True

    # https://stackoverflow.com/questions/10480806/compare-dictionaries-ignoring-specific-keys
    def equal_dicts(self, d1, d2, ignore_keys):
        ignored = set(ignore_keys)
        for k1, v1 in d1.items():
            if k1 not in ignored and (k1 not in d2 or d2[k1] != v1):
                return False
        for k2, v2 in d2.items():
            if k2 not in ignored and k2 not in d1:
                return False
        return True

    # https://stackoverflow.com/questions/273192/how-can-i-create-a-directory-if-it-does-not-exist
    async def write_dict(self, curr_text):
        # Create dir if it does not exist
        pathlib.Path(config.INPUT_TABLE_DIRECTORY).mkdir(parents=True, exist_ok=True)
        # Get filename
        filename = os.path.join(config.INPUT_TABLE_DIRECTORY,
                                'input_table_' + str(time.time()) + '.json')
        # Write dictionary
        with open(filename, 'w') as f:
            f.write(curr_text)
        # log.info("[City_HTTP] log file saved" + filename)

# myobjectx = City_HTTP("citymatrix", 0.5)

# myobjectx.start()
