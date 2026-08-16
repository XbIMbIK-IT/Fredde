from fredde import freddies
from fredde import Fredde
from sex import try_sex
import tree
from simulation import step
from freddePhoto import show_fredde
from freddePhoto import save_fredde

Ded1 = Fredde(
    name='Дедушка',
    color=[180, 200, 30],
    genid=10,
    gendom=0.3,
    mutrate=0,
    rarity='rare',
    age=10
)

Babka1 = Fredde(
    name='Бабушка',
    color=[40, 0, 135],
    genid=20,
    gendom=0.8,
    mutrate=0,
    rarity='common',
    age=10
)

Ded2 = Fredde(
    name='Другой дедушка',
    color=[55, 0, 0],
    genid=-30,
    gendom=0.3,
    mutrate=0,
    rarity='legendary',
    age=10
)

Babka2 = Fredde(
    name='Другая бабушка',
    color=[255, 0, 70],
    genid=-42,
    gendom=0.8,
    mutrate=0,
    rarity='mythic',
    age=10
)

baby, message = try_sex(Ded1, Babka1)

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

show_fredde(baby)

# tree.show()
