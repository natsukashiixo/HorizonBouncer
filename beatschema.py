import json
import copy
import datetime
from typing import Optional
import sklearn as sk
from collections import deque
import gzip

class BeatSchema:
    def __init__(self, bpm: int, rounding=1):

        self.ease = -1
        self.rounding = rounding
        self.bpm = bpm

        self.json_header = {
            "lane":0,
            "beat":0,
            "entities": []
        } # lane zero beat zero to make sure we always start from the beginning

        self.leveldata_header = {
            "bgmOffset":0,
            "entities":[
            {"archetype":"Initialization","data":[]},
            {"archetype":"Stage","data":[]},
            {"archetype":"#BPM_CHANGE","data":[{"name":"#BEAT","value":0},{"name":"#BPM","value":self.bpm}]},
            {"archetype":"#TIMESCALE_CHANGE","data":[{"name":"#BEAT","value":0},
            {"name":"#TIMESCALE","value":1}]},
            #{"archetype":"ShiftEvent","data":[]} this wrote an empty entry but instead of doing it properly i just commented it out lmao bow before my genius
            ]}

        self.leveldata_shift_event = {
            "archetype": "ShiftEvent",
            "data": [
                {"name": "#BEAT", "value": float},
                {"name": "value", "value": float},
                {"name": "ease", "value": int},
                {"name": "next", "ref": str}
            ],
            "name": str
        } # for reference

        self.shift_event = {
            "archetype":"ShiftEvent",
            "data":[
                {
                "name":"#BEAT",
                "value":float
                },
                {
                "name":"value",
                "value":float # value between 0 and 1
                },
                {
                "name":"ease",
                "value":int # -1 = ease out, 0 = linear, 1 = ease in
                }
            ]
        }

        self.entities_index = 0 # keep track of where you are
        self.entities_list = [] # to write directly into the header i guess

    @property
    def ease(self):
        return self._ease

    @ease.setter
    def ease(self, value: int):
        if not value in range(-1,2):
            raise ValueError("ease must be between -1 and 1")
        self._ease = value

    def add_shift_event(self, beat: float, value: float):
        # deep copy to not reference same object constantly
        new_shift_event = copy.deepcopy(self.shift_event)

        new_shift_event["data"][0]["value"] = beat
        new_shift_event["data"][1]["value"] = round(value, self.rounding)
        new_shift_event["data"][2]["value"] = self.ease
        
        self.entities_list.append(new_shift_event)
        self.entities_index += 1

    def validate_unique_shift_events(self):
        """
        Identifies redundant shift events while preserving the last event before a value change.
        This removes unnecessary events while maintaining proper transitions.
        """
        if not self.entities_list:
            return []  # No events to validate
            
        # Extract all shift events
        shift_events = []
        for event in self.entities_list:
            if event["archetype"] == "ShiftEvent":
                shift_events.append(event)
        
        if len(shift_events) <= 1:
            return []  # Need at least 2 shift events to compare
        
        # Find redundant events but keep the last one before a change
        redundant_events = []
        
        # Keep track of runs of identical values
        current_value = shift_events[0]["data"][1]["value"]
        current_run = [shift_events[0]]
        
        for i in range(1, len(shift_events)):
            this_value = shift_events[i]["data"][1]["value"]
            
            if this_value == current_value:
                # Add to the current run of identical values
                current_run.append(shift_events[i])
            else:
                # Value changed - mark all but the last event in the run as redundant
                if len(current_run) > 1:
                    redundant_events.extend(current_run[:-1])
                
                # Start a new run
                current_value = this_value
                current_run = [shift_events[i]]
        
        # Handle the final run
        if len(current_run) > 1:
            redundant_events.extend(current_run[:-1])
        
        return redundant_events
    
    def remove_redundant_shift_events(self):
        """
        Removes shift events that don't change the visual state (same value as previous).
        Returns the number of events removed.
        """
        redundant_events = self.validate_unique_shift_events()
        
        # Remove redundant events
        for event in redundant_events:
            self.entities_list.remove(event)
        
        # Update the index
        self.entities_index = len(self.entities_list)
        
        return len(redundant_events)

    def scale_minmax(self, rounding=True):
        basevals = [entity["data"][1]["value"] for entity in self.entities_list.copy()]
        scaled = sk.preprocessing.minmax_scale(basevals, feature_range=(0, 1))
        for i, entity in enumerate(self.entities_list):
            if rounding:
                entity["data"][1]["value"] = round(scaled[i], self.rounding)
            else:
                entity["data"][1]["value"] = scaled[i]
        return scaled

    def add_alignment_event(self):
        new_shift_event = copy.deepcopy(self.shift_event)
        new_shift_event["data"][0]["value"] = 0
        new_shift_event["data"][1]["value"] = 0
        new_shift_event["data"][2]["value"] = self.ease
        if not self.entities_list[0]["data"][0]["value"] == 0:
            dq = deque(self.entities_list)
            dq.appendleft(new_shift_event)
            self.entities_list = list(dq)
            return
        return
    
    def write_shift_event_references(self):
        maxlen = len(self.entities_list)
        # Create a reversed copy for iteration
        reversed_entities = self.entities_list.copy()
        reversed_entities.reverse()
        
        for i, entity in enumerate(reversed_entities):
            if i == 0:
                entity["name"] = hex(maxlen)  # First entity (last in original list)
                maxlen -= 1
            else:
                # Add reference to the previous entity (next in original order)
                ref_dict = {"name": "next", "ref": hex(maxlen+1)}
                entity["data"].append(ref_dict)
                entity["name"] = hex(maxlen)
                maxlen -= 1
        
        reversed_entities.reverse()
        self.entities_list = reversed_entities
        return

    def write_to_leveldata(self, filename: Optional[str] = None):
        self.write_shift_event_references()  # Only used here so only called in here
        if not filename:
            now = datetime.datetime.now()
            filename = f"{now.day}-{now.month}-{now.year}_output.json"
        header = copy.deepcopy(self.leveldata_header)
        print(header)
        shiftevent_data = self.entities_list.copy()
        print('-------------------------------------------------------------------------')
        header["entities"].extend(shiftevent_data)
        print(header)
        json_data = json.dumps(header, indent=0)  # 0 indent for compression reasons
        with gzip.open(filename, "wb") as f:
            f.write(json_data.encode("utf-8"))

    def write_to_json(self, filename: Optional[str] = None):
        if not filename:
            now = datetime.datetime.now()
            filename = f"{now.day}-{now.month}-{now.year}_output.json"
        self.json_header["entities"] = self.entities_list
        with open(filename, "w") as f:
            json.dump(self.json_header, f, indent=4)
