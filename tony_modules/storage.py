import json


class JSONStore():
    '''
    A corutine-safe wrapper for a json file
    To stay corutine-safe there must be only be one instance 
    of a JSONStore per json file
    '''

    def __init__(self, file_name):
        self._file = file_name
    
    def _read_file(self):
        try:
            with open(self._file, 'r') as f:
                return json.loads(f.read())
        except FileNotFoundError:
            return {}
    
    def read(self, key): #seperate set and get functions for when get item and set item are too confusing (ie, for cases when sync() is useful)
        return self._read_file().get(key) #read file every time because we want to be able to edit config files manually

    def write(self, key, value):
        if not isinstance(key, str):
            raise ValueError('Sorry, JSON can only store string keys')
        data = self._read_file() #re-read whole file in case it was changed manually
        data[key] = value
        with open(self._file, 'w') as json_file:
            json_file.write(json.dumps(data))
        
    def __setitem__(self, key, value):
        self.write(key, value)

    def __getitem__(self, key):
        return self.read(key)