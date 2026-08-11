import random
from fredde import Fredde
from sex import SEX
import tree

with open("NameList.txt", 'r') as f:
    NameList = f.read().splitlines()


Ded1 = Fredde(
    'Дедушка',
    color=[255, 20, 0],
    genid=10,
    gendom=0.3,
    mutrate=0,
    rarity='rare'
)

Babka1 = Fredde(
    'Бабушка',
    color=[40, 0, 200],
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

Fred1 = SEX(Ded1, Babka1, random.choice(NameList))

Fred2 = SEX(Ded2, Babka2, random.choice(NameList))

baby = SEX(Fred1, Fred2, random.choice(NameList))

print(baby.name)
print(baby.generation)
print(baby.genid)
print(baby.gendom)
print(baby.mutrate)
print(baby.color)
print(baby.rarity)

tree.show()