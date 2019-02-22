import json


class JSONStore:
        
    def __init__(self, file_name):
        self._file = file_name
        try:
            with open(file_name, 'r') as f:
                self._store = json.loads(f.read())
        except FileNotFoundError:
            self._store = dict()
        
    def __setitem__(self, key, value):
        if not type(key) == str:
            raise Exception('Sorry, JSON can only store string keys')
        self._store[key] = value
        self.update()
            
    def __getitem__(self, key):
        return self._store.get(key)

    def update(self):
        '''updates the contents of the json file
            called when setting an item via __setitem__
            useful when storing mutable objects, ie:
            store['list'].append('item'); store.update()'''
        with open(self._file, 'w') as f:
            f.write(json.dumps(self._store))
