# importing the requests library
import os
import sys
import json
import time
import config
import logging
import pathlib
import requests
from cityiograph import City

log = logging.getLogger('__main__')

class City_HTTP():

    def __init__(self):
        self.URL_get = "https://cityio.media.mit.edu/api/table/" + config.CITYIO_GET_TABLE
        self.URL_post = "https://cityio.media.mit.edu/api/table/update/" + config.CITYIO_POST_TABLE
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
            self.write_dict(curr_text)
            self.prev_text = curr_text
            self.prev_json = curr_json
            log.info("[City_HTTP] New data")
            return City(curr_text)

    def post_table(self, data):
        log.info(json.dumps(data))
        r = requests.post(url = self.URL_post, json = data)
        log.info(r)
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
    def write_dict(self, curr_text):
        # Create dir if it does not exist
        pathlib.Path(config.INPUT_TABLE_DIRECTORY).mkdir(parents=True, exist_ok=True)

        # Get filename
        filename = os.path.join(config.INPUT_TABLE_DIRECTORY,
                                'input_table_' + str(int(time.time())) + '.json')

        # Write dictionary
        with open(filename, 'w') as f:
            f.write(curr_text)

# myobjectx = City_HTTP("citymatrix", 0.5)

# myobjectx.start()
