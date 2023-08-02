from dataclasses import dataclass
import numpy as np

@dataclass
class EV:
    time_required: list
    power_required: list
    max_power: int
    
    original_time_required: list = None

    def __post_init__(self):
        if len(self.time_required) == len(self.power_required):
            self.total_power = sum(self.power_required)
            self.number_of_evs = len(self.power_required)
            self.original_time_required = self.time_required.copy()
            self.time_required = 1 / np.array(self.time_required)
        else:
            raise ValueError("Time and power requirements must be of same length. The number of EVs is corresponding to the length of the lists.")
        
