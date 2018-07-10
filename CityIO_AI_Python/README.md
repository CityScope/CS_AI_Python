# New CityIO_AI Design & Data Format
07/05/2018&emsp;&emsp;'Ryan' Yan Zhang, Yifan Meng

Current version: 1.0 (07/05/2018)
<br><br>
## 1. Background
 The long term plan for CityMatrix is to have a modularized design which separates the whole project into four different modules: input, output, data processing, and data storage. To achieve reliability, performance, and modularity of CityMatrix, we redesigned CityMatrix_AI to adapt the overall roadmap. 
<br><br>
## 2. Structure
CityIO_AI will take over all the data processing jobs in the CityMatrix ecosystem
<br><br>
![CityMatrix Flowchart](flowchart.svg "CityMatrix Flowchart")
>1. **Input Module** will only gather raw input data and store it into the *Input Table* of **CityIO**<br>
>2. **CityIO_AI** monitors the *Input Table* of CityIO and will start the computing process whenever it gets new data from *Input Table*<br>
>3. When calculation is done, **CityIO_AI** puts the result into the *Output Table* of **CityIO**
>4. **Output Module** monitors the *Output Table* of **CityIO** to display the latest calculation result

Each module is highly specialized and optimized to do its own job. This design allows minimal data transmission in small packets to achieve low latency and smooth visualization

### CityIO Table Naming Convention
Input table endpoint: `.../table/update/{proj_name}_in`<br>
Output table endpoint: `.../table/{proj_name}_out`<br>
>E.g.: For a project called **CityMatrix**, input data should be [POST] to https://cityio.media.mit.edu/api/table/update/CityMatrix_in and output result can be [GET] from https://cityio.media.mit.edu/api/table/CityMatrix_out<br>
>(Endpoint path in this example is updated for CityIO version 2.1)

You can always find the latest CityIO API endpoints [here](https://github.com/CityScope/CS_CityIO_Backend/wiki/API)
<br><br>
## 3. Input data format
Below are the definitions of keys crucial to the input JSON; For those keys not defined in this list, check [**Section 5**](#5-cityio-minimal-json-format) for default CityIO format. 

+ **meta**
+ **header**
    <a id="header_block"></a>
    + **block**: `array` of `string`s, define the data contained in each grid
        + Current input JSON contains 2 values: `"block":["type","rot"]`
    + **mapping**: `object` of `object`s, mapping of the values of specified data defined in the `block` array
        + **type**: each optical tag can be decoded into an `int` value; this object explains type of the cell each value stands for
        <a id="rot_mapping"></a>
        + **rot**: rotation of each brick is stored as an `unsigned int` value; value stands for <u>counterclockwise rotation in degree</u>
        + Current version contains 2 objects: `"mapping":{"type":{"0":"RL",...},"rot":{"0":0,...}}` (see [Sample JSON](#sample_json_input) for detail)
+ **grid**: `array` of `object`s, each object has the keys defined in the [block](#header_block) array; data is order as a row by row basis starting from the top row: first object is for the top left corner of the table, which is (0,0); second is (1,0) so on so forth
    ```
    Order of grid objects for 4 by 4 table: 
     ⇢ x
    ⇣ |  0 |  1 |  2 |  3 |
    y |  4 |  5 |  6 |  7 |
      |  8 |  9 | 10 | 11 |
      | 12 | 13 | 14 | 15 |
    ```
    + **type**: an `int` value between `-1` and `7`, indicates the type of that cell
    + **rot**: an `unsigned int` value between `0` and `3`, indicates the rotation of that cell
+ **objects**
    + **AIWeights**: an object of key-value pairs includes all the urban performances, values are `float`s between `0.0` and `1.0`
        + Current version contains 5: density, diversity, energy, traffic, solar
    + **dockID**: an `int` value between `-1` and `7`, indicates the optical tag ID of the current dock block
    + **dockRot**: an `unsigned int` value between `0` and `3`, indicates the counterclockwise rotation of the dock block (rotation mapping defined [here](#rot_mapping))
    + **density**: a `float` value between `0.0` and `1.0`, indicates the input value from density slider
    + **heatmap**: a `float` value between `0.0` and `1.0`, indicates the input value from heatmap slider
    + **toggle**: a `bool` value, indicates the status of the toggle slider
    + **timestamp**: a `long` value, indicates the send time of this JSON from the input module, also the latest input data update time (unix time in milliseconds)

<a id="sample_json_input"></a>
### Sample JSON:
&emsp;*Minimal requirement of data format V1.0*
```json
{
    "meta":{},
    "header":{
        "name":,
        "spatial":{},
        "owner":{},
        "block":["type","rot"],
        "mapping":{
            "type":{
                "-1":"EMPTY",
                "0":"RL",
                "1":"RM",
                "2":"RS",
                "3":"OL",
                "4":"OM",
                "5":"OS",
                "6":"ROAD",
                "7":"PARK"
            },
            "rot":{
                "0":0,
                "1":90,
                "2":180,
                "3":270,
            }
        }
    },
    "grid":[
        {"type": -1, "rot":0},
        {"type": -1, "rot":0}
    ],
    "objects":{
        "AIWeights":{
            "density":0.0,
            "diversity":0.0,
            "energy":0.0,
            "traffic":0.0,
            "solar":0.0
        },
        "dockID":0,
        "dockRot":0,
        "heatmap":0.0,
        "density":0.0,
        "toggle":false,
        "timestamp":1530763200000
    }
}
```
<br><br>
## 4. Output data format
Below are the definitions of keys crucial to the output JSON; For those keys not defined in this list, check [**Section 5**](#5-cityio-minimal-json-format) for default CityIO format. 

+ **meta**
+ **header**
    + **block**: array of strings, define the data contained in each grid
        + Current output JSON contains 3 values: `"block":["type","rot","data"]`
+ **grid**: `array` of `object`s, each object has the keys defined in the [block](#header_block) array
    + **type**: an `int` value between `-1` and `7`, indicates the type of that cell
    + **rot**: an `unsigned int` value between `0` and `3`, indicates the rotation of that cell
    + **data**: an object includes all the urban performances, values are `float`s between `0.0` and `1.0` indicate calculated values for each cell
        + Current version contains 5: density, diversity, energy, traffic, solar
+ **objects**
    + **metrics**: an object of key-value pairs includes data for radar chart visualization, keys are all the urban performances and values are `float`s between `0.0` and `1.0` indicate calculated values for each cell
    + **densities**: an object of key-value pairs includes density values for all types of buildings, keys are building types and values are `unsigned int` values between `1` and `30`
    + **AIMove**: an object include the AI suggestion of next move, there are 2 different cases:
        + **moveType**: one of these two `string`s: `"cell"` or `"density"`, indicates the type of suggested move. 
            + If this value is `"cell"`, `x` and `y` will be the coordinate of the target cell, and `bldgType` will be the suggested type of building to be put at the specified coordinate (in this case `value` does not have meaningful data)
            + If this value is`"density"`, `bldgType` will be the suggested type of building to adjust, `value` will be the suggested new density value for that type of building (in this case `x` and `y` do not have meaningful data)
        + **bldgType**: an `int` value between `0` and `5`
        + **value**: an `unsigned int` value between `1` and `30`
        + **x**: an `int` value
        + **y**: an `int` value
    + **tutorialStep**: an `int` value, indicates the current step of tutorial
    + **timestamp**: a `long` value, indicates the send time of this JSON from **CityIO_AI**, also the latest output data update time (unix time in milliseconds)

<a id="sample_json_input"></a>
### Sample JSON:
&emsp;*Minimal requirement of data format V1.0*
```json
{
    "meta":{},
    "header":{
        "name":,
        "spatial":{},
        "owner":{},
        "block":["type","rot","data"],
        "mapping":{
            "type":{
                "-1":"EMPTY",
                "0":"RL",
                "1":"RM",
                "2":"RS",
                "3":"OL",
                "4":"OM",
                "5":"OS",
                "6":"ROAD",
                "7":"PARK"
            },
            "rot":{
                "0":0,
                "1":90,
                "2":180,
                "3":270,
            }
        }
    },
    "grid":[
        {
            "type": -1,
            "rot":0,
            "data":{
                "density":0.0,
                "diversity":0.0,
                "energy":0.0,
                "traffic":0.0,
                "solar":0.0
            }
        },
        {
            "type": -1,
            "rot":0,
            "data":{
                "density":0.0,
                "diversity":0.0,
                "energy":0.0,
                "traffic":0.0,
                "solar":0.0
            }
        }
    ],
    "objects":{
        "metrics":{
            "density":0.0,
            "diversity":0.0,
            "energy":0.0,
            "traffic":0.0,
            "solar":0.0
        },
        "densities":{
            "0":0,
            "1":0,
            "2":0,
            "3":0,
            "4":0,
            "5":0,
        },
        "AIMove":{
            "moveType":"cell",
            "bldgType":0,
            "value":0,
            "x":0,
            "y":0
        },
        "tutorialStep":0,
        "timestamp":1530763200000
    }
}
```
<br><br>
## 5. CityIO Minimal JSON Format
*As of CityIO Version 2.1*

If an empty JSON is received by **CityIO**, it will be auto-completed and stored into *Input Table* as follow: 

>timestamp is auto appended to a new incoming JSON data by the CityIO server at the time it receives the data; thus the timestamp is not local time but server time (unix time in milliseconds)
``` json
{
    "meta":{
        "id": "",
        "timestamp": 1530306513043,
        "apiv": ""
    },
    "header":{
        "name":"",
        "spatial":{
            "nrows":0,
            "ncols":0,
            "physical_longitude":0,
            "physical_latitude":0,
            "longitude":0,
            "latitude":0,
            "cellSize":0,
            "rotation":0
        },
        "owner":{
            "name":"",
            "title":"",
            "institute":""
        },
        "block":null,
        "mapping":null
    },
    "grid":null,
    "objects":null
}
```
