class Dummy():
    ...

def dict2class(data, _class=Dummy()):
    for k, v in data.items():
        if isinstance(v, dict):
            __class = dict2class(v)
            setattr(_class, k, __class)
        else:
            setattr(_class, k, v)
    return _class