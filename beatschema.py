import json
import copy
import datetime
from typing import Optional

class BeatSchema:
    def __init__(self, rounding=2):

        self.ease = -1
        self.rounding = rounding

        self.json_header = {
            "lane":0,
            "beat":0,
            "entities": []
        } # lane zero beat zero to make sure we always start from the beginning

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
        Identifies and returns shift events that have the same value as their previous event.
        This allows for removing redundant events that don't change the visual state.
        """
        if not self.entities_list:
            return []  # No events to validate
            
        # Group events by archetype
        shift_events = []
        for event in self.entities_list:
            if event["archetype"] == "ShiftEvent":
                shift_events.append(event)
        
        if len(shift_events) <= 1:
            return []  # Need at least 2 shift events to compare
        
        # Find events with same value as previous
        redundant_events = []
        for i in range(1, len(shift_events)):
            current_value = shift_events[i]["data"][1]["value"]
            previous_value = shift_events[i-1]["data"][1]["value"]
            
            if current_value == previous_value:
                redundant_events.append(shift_events[i])
        
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
    
    def write_to_json(self, filename: Optional[str] = None):
        if not filename:
            now = datetime.datetime.now()
            filename = f"{now.day}-{now.month}-{now.year}_output.json"
        self.json_header["entities"] = self.entities_list
        with open(filename, "w") as f:
            json.dump(self.json_header, f, indent=4)
