
import os, sys

def package_home(gdict):
    filename = gdict["__file__"]
    return os.path.dirname(filename)

class Resource(object):

    def __init__(self, filename, _prefix=None):
        path = self.get_path_from_prefix(_prefix)
        self.filename = os.path.join(path, filename)
        if not self.checkResource():
            raise ValueError("No such resource", self.filename)

    def get_path_from_prefix(self, _prefix):
        if isinstance(_prefix, str):
            path = _prefix
        else:
            if _prefix is None:
                _prefix = sys._getframe(2).f_globals
            path = package_home(_prefix)
        return path

    def checkResource(self):
        return True


class DirectoryResource(Resource):
        
    def checkResource(self):
        return os.path.isdir(self.filename)

    def list(self):
        return os.listdir(self.filename)

    def path(self):
        return self.filename

class FileResource(Resource):
    
    def open(self, mode="r"):
        return open(self.filename, mode)

    def checkResource(self):
        return os.path.isfile(self.filename)
