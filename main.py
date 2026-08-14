import random
from fredde import Fredde
from sex import TrySex
import tree

Ded1 = Fredde(
    'Дедушка',
    color=[180, 200, 30],
    genid=10,
    gendom=0.3,
    mutrate=0,
    rarity='rare'
)

Babka1 = Fredde(
    'Бабушка',
    color=[40, 0, 135],
    genid=20,
    gendom=0.8,
    mutrate=0,
    rarity='common'
)

Ded2 = Fredde(
    'Другой дедушка',
    color=[55, 0, 0],
    genid=-30,
    gendom=0.3,
    mutrate=0,
    rarity='legendary'
)

Babka2 = Fredde(
    'Другая бабушка',
    color=[255, 0, 70],
    genid=-42,
    gendom=0.8,
    mutrate=0,
    rarity='mythic'
)

baby = TrySex(Ded1, Babka1)

print(baby.name)
print(baby.gender)
print(baby.age)
print(baby.generation)
print(baby.genid)
print(baby.gendom)
print(baby.mutrate)
print(baby.color)

tree.show()
