import json


class JSONStore():
    '''
    A wrapper for a json file
    Individual reads and writes are coroutine safe
    HOWEVER (just like a regular file) if you read and then await an
        async function you should assume that your last read is now
        out of date (whether that matters depends on the context)
    '''


    def __init__(self, file_name):
        self._file = file_name
    

    def _read_file(self):
        try:
            with open(self._file, 'r') as f:
                return json.loads(f.read())
        except FileNotFoundError:
            return {}
    

    def read(self, key=None): #seperate set and get functions for when get item and set item are too confusing (ie, for cases when sync() is useful)
        '''reads the specified key
        if key is not specified then the entire json object is returned'''
        
        data = self._read_file() #read file every time because we want to be able to edit config files manually
        if key is not None:
            return self._read_file().get(key)
        return data


    def write(self, key, value):
        '''writes the specified key to the json file'''

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