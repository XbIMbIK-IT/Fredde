from Fredde import freddies
from fredde import Fredde
from sex import TrySex
import tree
from step import Step

Ded1 = Fredde(
    'Дедушка',
    color=[180, 200, 30],
    genid=10,
    gendom=0.3,
    mutrate=0,
    rarity='rare',
    age=10
)

Babka1 = Fredde(
    'Бабушка',
    color=[40, 0, 135],
    genid=20,
    gendom=0.8,
    mutrate=0,
    rarity='common',
    age=10
)

Ded2 = Fredde(
    'Другой дедушка',
    color=[55, 0, 0],
    genid=-30,
    gendom=0.3,
    mutrate=0,
    rarity='legendary',
    age=10
)

Babka2 = Fredde(
    'Другая бабушка',
    color=[255, 0, 70],
    genid=-42,
    gendom=0.8,
    mutrate=0,
    rarity='mythic',
    age=10
)

baby, message = TrySex(Ded1, Babka1)

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

Step(freddies)
Step(freddies)

print(baby.age)

tree.show()
