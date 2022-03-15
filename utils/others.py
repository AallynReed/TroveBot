from string import ascii_letters, digits
from random import choices

def RandomID(size=8):
    return "".join(choices(ascii_letters+digits, k=size))