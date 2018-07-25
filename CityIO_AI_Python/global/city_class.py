import sys
import os
import json
import time
import datetime
import config
import logging
import pathlib
import numpy as np
sys.path.append('../CityMAItrix/')
from objective import objective
log = logging.getLogger('__main__')

class InputCity(object):
    """InputCity Class
    
    Arguments:
        object {class} -- city class
    """
    def __init__(self, json_string):
        """Store json data
        
        Arguments:
            json_string {json} -- json string
        """
        self.densities = [1] * 6
        self.json_update(json_string)

    def json_update(self, json_string):
        # update variables
        self.json_obj = json.loads(json_string)
        self.meta = self.json_obj['meta']
        self.header = self.json_obj['header']
        self.nrows = self.json_obj['header']['spatial']['nrows']
        self.ncols = self.json_obj['header']['spatial']['ncols']
        self.ai_density = self.json_obj['objects']['AIWeights']['density']
        self.ai_diversity = self.json_obj['objects']['AIWeights']['diversity']
        self.ai_energy = self.json_obj['objects']['AIWeights']['energy']
        self.ai_solar = self.json_obj['objects']['AIWeights']['solar']
        self.ai_traffic = self.json_obj['objects']['AIWeights']['traffic']
        self.density = self.json_obj['objects']['density']
        self.dock_id = self.json_obj['objects']['dockID']
        self.dock_rot = self.json_obj['objects']['dockRot']
        self.heatmap = self.json_obj['objects']['heatmap']
        self.toggle = self.json_obj['objects']['toggle']
        self.client_ts = self.json_obj['objects']['timestamp']
        self.server_ts = self.json_obj['meta']['timestamp']
        self.cells = get_cells_from_json(self.nrows, self.ncols, self.json_obj['grid'])
        # Save densities
        self.densities[self.dock_id] = self.density
    
    def equals(self, other):
        cells_equal = all([c.equals(other.cells[pos]) for pos, c in enumerate(self.cells)])
        return (cells_equal and 
                self.densities == other.densities and 
                self.dock_id == other.dock_id and 
                self.ai_density == other.ai_density and 
                self.ai_diversity == other.ai_diversity and 
                self.ai_energy == other.ai_energy and 
                self.ai_solar == other.ai_solar and 
                self.ai_traffic == other.ai_traffic)

    def get_population(self):
        # Assumption: each cell is 1 km^2
        pop = 0
        for cell in self.cells:
            cell_type = cell.get_type()
            if cell_type >=0 and cell_type <=5:
                pop += self.densities[cell_type] * cell.get_pplfloor()
        return pop
    
    def get_traffic(self):
        features = []
        for cell in self.cells:
            cell_feature = []
            cell_type = cell.get_type()
            if cell_type >=0 and cell_type <=5:
                cell_feature.append(self.densities[cell_type] * cell.get_pplfloor())
            else:
                cell_feature.append(0)
            if cell_type == 6:
                cell_feature.append(0)
            else:
                cell_feature.append(1)
            features.append(cell_feature)

        return np.array(features).flatten()

    def get_solar(self):
        features = []
        for cell in self.cells:
            cell_feature = 0.0
            cell_type = cell.get_type()
            if cell_type >=0 and cell_type <=5:
                cell_feature = self.densities[cell_type] * config.DENSITY_TO_HEIGHT_FACTOR
            else:
                cell_feature = 0
            features.append(cell_feature)

        return np.array(features).flatten()

class OutputCity(object):
    def __init__(self, input_city):
        """Store json data
        
        Arguments:
            json_string {json} -- json string
        """
        self.json_obj = input_city.json_obj
        self.new_json_obj = {}
        self.meta = input_city.meta
        self.header = input_city.header
        self.nrows = input_city.nrows
        self.ncols = input_city.ncols
        self.density = input_city.density
        self.dock_id = input_city.dock_id
        self.dock_rot = input_city.dock_rot
        self.heatmap = input_city.heatmap
        self.toggle = input_city.toggle
        self.cells = input_city.cells
        self.densities = input_city.densities
        self.input_ts = input_city.client_ts
        self.output_ts = 0
        self.metrics = {
            "density":0.0,
            "diversity":0.0,
            "energy":0.0,
            "traffic":0.0,
            "solar":0.0
        }
        self.pop_array = np.zeros((self.nrows, self.ncols, 6))
    
    def get_pop_obj(self):
        # Assumption: each cell is 1 km^2
        pop = {0:0, 1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0, -1:0}
        for cell in self.cells:
            cell_type = cell.get_type()
            if cell_type >=0 and cell_type <=5:
                # pop += self.densities[cell_type] * cell.get_pplfloor()
                pop[cell_type] += self.densities[cell_type] * cell.get_pplfloor()
        return pop

    def calc_density(self):
        for cell in self.cells:
            cell_type = cell.get_type()
            if cell_type >=0 and cell_type <=5:
                cell.set_density(self.densities[cell_type] * cell.get_pplfloor())
            else:
                cell.set_density(0)
            
    def calc_diversity(self):
        for cell in self.cells:
            self.cell_diversity(cell)
    
    def cell_diversity(self, cell):
        DIV_RADIUS = 3
        temp_pop = np.zeros(6)
        low_x = ( 0
            if cell.x < DIV_RADIUS 
            else cell.x - DIV_RADIUS )
        high_x = ( self.ncols -1 
            if cell.x > self.ncols - DIV_RADIUS -1
            else cell.x + DIV_RADIUS )
        low_y = ( 0
            if cell.y < DIV_RADIUS 
            else cell.y - DIV_RADIUS )
        high_y = ( self.nrows -1 
            if cell.y > self.nrows - DIV_RADIUS -1
            else cell.y + DIV_RADIUS )
        for temp_x in range(low_x, high_x + 1):
            for temp_y in range(low_y, high_y + 1):
                temp_cell = self.cells[temp_x + temp_y * self.ncols]
                cell_type = temp_cell.get_type()
                if cell_type >=0 and cell_type <=5:
                    temp_pop[cell_type] += self.densities[cell_type] * config.DENSITY_TO_HEIGHT_FACTOR
        residential_diversity = LUM([temp_pop[0], temp_pop[1], temp_pop[2]])
        office_diversity = LUM([temp_pop[3], temp_pop[4], temp_pop[5]])
        living_working_diversity = LUM([temp_pop[0] + temp_pop[1] + temp_pop[2],
                                    temp_pop[3] + temp_pop[4] + temp_pop[5]])
        cell.set_diversity((residential_diversity + office_diversity +
                            living_working_diversity) / 3.0)
    
    def calc_energy(self):
        energy_per_sqm = [-0.2, 0.0, 0.2, -0.4, 0.0, 0.4]
        floor_area = 1562.5 # square meters
        for cell in self.cells:
            cell_type = cell.get_type()
            if cell_type >=0 and cell_type <=5:
                cell.set_energy(self.densities[cell_type] * floor_area * energy_per_sqm[cell_type])
            else:
                cell.set_energy(-6000)

    def set_traffic(self, traffic_output):
        i = 0
        for cell in self.cells:
            cell.set_traffic(round(traffic_output[i], 2))
            i += 2
    
    def set_solar(self, solar_output):
        i = 0
        for cell in self.cells:
            cell.set_solar(round(solar_output[i], 2))
            i += 1

    def set_metrics(self, metricsArray):
        self.metrics["density"] = metricsArray[0]
        self.metrics["diversity"] = metricsArray[1]
        self.metrics["energy"] = metricsArray[2]
        self.metrics["traffic"] = metricsArray[3]
        self.metrics["solar"] = metricsArray[4]
    
    def set_ts(self):
        now = datetime.datetime.now()
        self.output_ts = int(time.mktime(now.timetuple())*1e3 + now.microsecond/1e3)
    
    def get_json_obj(self):
        return self.new_json_obj

    def to_json(self):
        self.new_json_obj['meta'] = self.meta
        self.new_json_obj['header'] = self.header
        self.new_json_obj['header']['block'].append("data")
        self.new_json_obj['grid'] = []
        self.new_json_obj['objects'] = {}
        self.new_json_obj['objects']['dockID'] = self.dock_id
        self.new_json_obj['objects']['dockRot'] = self.dock_rot
        self.new_json_obj['objects']['heatmap'] = self.heatmap
        self.new_json_obj['objects']['density'] = self.density
        self.new_json_obj['objects']['tutorialStep'] = 0
        self.new_json_obj['objects']['timestamp'] = self.output_ts
        self.new_json_obj['objects']['timestamp_in'] = self.input_ts
        self.new_json_obj['objects']['densities'] = {str(i):self.densities[i] for i in range(0,6)}
        self.new_json_obj['objects']['metrics'] = self.metrics
        for cell in self.cells:
            self.new_json_obj['grid'].append(cell.to_json())
        return json.dumps(self.new_json_obj)

class Cell(object):

    def __init__(self, x, y, json_data):
        self.x = x
        self.y = y
        self._type = json_data['type']
        self._rot = json_data['rot']
        self._density = 0.0
        self._diversity = 0.0
        self._energy = 0.0
        self._traffic = 0.0
        self._solar = 0.0

    def equals(self, other):
        return self._type == other.get_type()

    def get_pos(self):
        return (self.x, self.y)

    def get_type(self):
        return self._type
    
    def get_pplfloor(self):
        if self._type >=0 and self._type <=5:
            return config.POP_ARR[self._type]
        else:
            return 0
    
    def get_density(self):
        return self._density

    def get_diversity(self):
        return self._diversity

    def get_energy(self):
        return self._energy
    
    def get_traffic(self):
        return self._traffic

    def get_solar(self):
        return self._solar
    
    def set_density(self, density):
        self._density = normalize(density, 0, 390)
    
    def set_diversity(self, diversity):
        self._diversity = normalize(diversity, 0.65, 1.0)

    def set_energy(self, energy):
        self._energy = normalize(energy, -6000, 6000)

    def set_traffic(self, traffic):
        self._traffic = normalize(traffic, 1000, 3000)
    
    def set_solar(self, solar):
        self._solar = normalize(solar, 1000, 1300)
    
    def to_json(self):
        return {
            "type":self._type, 
            "rot":self._rot, 
            "data":{
                "density":self._density,
                "diversity":self._diversity,
                "energy":self._energy,
                "traffic":self._traffic,
                "solar":self._solar
            }
        }

def get_cells_from_json(nrows, ncols, json_data):
    """Get Cell data from json input
    
    Arguments:
        json_data {json} -- grid data
    
    Returns:
        array -- array of `Cells`
    """
    cells = []
    cell_x = 0
    cell_y = 0
    for each_cell in json_data:
        c = Cell(cell_x, cell_y, each_cell)
        cells.append(c)
        cell_x += 1
        if cell_x >= ncols:
            cell_x = 0
            cell_y += 1
    return cells

def get_dict_from_cells(cells):
    cell_dict = {}
    for cell in cells:
        cell_dict[cell.get_pos()] = cell
    return cell_dict

def normalize(x, min, max):
    return (x - min) / (max - min)

def LUM(populations):
    #print(populations)
    tot = sum(populations)
    probs = map(lambda x: (x / tot) * np.log10(x / tot) if x != 0 else 0, populations)
    return -sum(probs) / np.log10(len(populations))