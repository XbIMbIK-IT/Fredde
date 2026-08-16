from fredde import freddies
from fredde import fredde
from sex import trySex
import tree
from simulation import step
from freddePhoto import show_fredde
from freddePhoto import save_fredde

Ded1 = fredde(
    name='Дедушка',
    eyelash= False,
    eye= 'blackout',
    hatAcs= 'foil',
    faceAcs= 'tube',
    bodyPattern= 'afghanistan',
    color=[180, 200, 30],
    genid=10,
    gendom=0.3,
    mutrate=0,
    rarity='rare',
    age=10
)

Babka1 = fredde(
    name='Бабушка',
    eyelash= False,
    eye= 'hearts',
    hatAcs= 'wings',
    faceAcs= 'tail',
    bodyPattern= 'hearts',
    color=[150, 10, 10],
    genid=20,
    gendom=0.8,
    mutrate=100,
    rarity='common',
    age=10
)

Ded2 = fredde(
    name='Другой дедушка',
    color=[55, 0, 0],
    genid=-30,
    gendom=0.3,
    mutrate=110,
    rarity='legendary',
    age=10
)

Babka2 = fredde(
    name='Другая бабушка',
    color=[255, 0, 70],
    genid=-42,
    gendom=0.8,
    mutrate=0,
    rarity='mythic',
    age=10
)

baby, message = trySex(Ded1, Babka1)

print(message)

if baby:
    values = [
        ("name", baby.name),
        ("gender", baby.gender),
        ("eyelashes", baby.eyelash),
        ("age", baby.age),
        ("generation", baby.generation),
        ("genid", baby.genid),
        ("gendom", baby.gendom),
        ("mutrate", baby.mutrate),
        ("color", baby.color)
    ]

    for name, value in values:
        print(f"{name}: {value}")

# step(freddies)
# step(freddies)
# print(baby.age)

#show_fredde(Babka1)

tree.show()
