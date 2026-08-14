import random

MAX_AGE = 25

def CheckDeath(freddies):
    for freddie in freddies:
        if freddie.alive:
            max_age = MAX_AGE * (1 - freddie.MutRate / 100)

            if freddie.age > max_age:
                if random.random() < 0.5:
                    freddie.alive = False


def Step(freddies):
    CheckDeath(freddies)

    for freddie in freddies:
        if freddie.alive:
            freddie.age += 1
