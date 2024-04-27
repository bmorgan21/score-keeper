import json
import os


VALUES = {}

def load(filename='data/settings.json'):
    global VALUES
    try:
        file = open(filename)
    except OSError:
        return
    
    try:
        values = json.loads(file.read())
    except ValueError:
        return
    
    VALUES = {}
    VALUES.update(values)
    
def makedirs(path):
    path_split = path.split('/')
    
    for i in range(len(path_split)):
        dname = '/'.join(path_split[:i+1])
        try:
            os.mkdir(dname)
        except OSError:
            pass
    
def save(filename='data/settings.json'):
    f_split = filename.rsplit('/', 1)
    if len(f_split) == 2:
        dname, fname = f_split
    else:
        dname, fname = None, f_split[0]
    
    makedirs(dname)
    
    f = open(filename, 'w')
    f.write(json.dumps(VALUES))
    f.close()
    
def get(key, default=None):
    return VALUES.get(key, default)

def set(key, value):
    VALUES[key] = value