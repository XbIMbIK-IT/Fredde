from fredde import freddies
from fredde import fredde
from sex import trySex
import tree
from simulation import step

Ded1 = fredde(
    'Дедушка',
    color=[180, 200, 30],
    genid=10,
    gendom=0.3,
    mutrate=0,
    rarity='rare',
    age=10
)

Babka1 = fredde(
    'Бабушка',
    color=[40, 0, 135],
    genid=20,
    gendom=0.8,
    mutrate=0,
    rarity='common',
    age=10
)

Ded2 = fredde(
    'Другой дедушка',
    color=[55, 0, 0],
    genid=-30,
    gendom=0.3,
    mutrate=0,
    rarity='legendary',
    age=10
)

Babka2 = fredde(
    'Другая бабушка',
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

step(freddies)
step(freddies)

print(baby.age)

tree.show()
