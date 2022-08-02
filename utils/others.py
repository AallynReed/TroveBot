import re
from random import choices
from string import ascii_letters, digits


def RandomID(size=8):
    return "".join(choices(ascii_letters+digits, k=size))

class Config:
    def __init__(self, data: dict=None):
        if data:
            for k, v in data.items():
                self._set_config(self._check_key(k), v)
                
    def __repr__(self):
        return str(self.as_dict())

    def _check_key(self, key: str):
        if not re.match("^[a-z_][a-z0-9_]*$", key, re.IGNORECASE):
            raise Exception("Key names must be valid python variable names")
        return key
    
    def _set_config(self, key: str, value):
        if isinstance(value, dict):
            value = Config(value)
        self.__dict__[self._check_key(key)] = value
        
    def _get_config(self, key: str):
        return self.__dict__[key]
        
    def _del_config(self, key: str):
        del self.__dict__[key]
    
    def as_dict(self):
        return {k: (v.as_dict() if isinstance(v, Config) else v) for k, v in self.__dict__.items()}
        