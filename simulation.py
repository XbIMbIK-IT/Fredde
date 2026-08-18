import random



def step(freddies):
    for freddie in freddies:
        if freddie.check_death():
            freddie.age += 1
