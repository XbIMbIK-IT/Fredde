from fredde import freddies
from fredde import fredde
from sex import try_sex
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
    color=[255, 255, 0],
    genid=10,
    gendom=0.3,
    mutrate=0,
    rarity='rare',
    age=11
)

Babka1 = fredde(
    name='Бабушка',
    eyelash= False,
    eye= 'hearts',
    hatAcs= 'wings',
    faceAcs= 'tail',
    bodyPattern= 'hearts',
    color=[255, 0, 0],
    genid=20,
    gendom=0.8,
    mutrate=0,
    rarity='common',
    age=11
)

Ded2 = fredde(
    name='Другой дедушка',
    color=[0, 255, 0],
    genid=-30,
    gendom=0.3,
    mutrate=0,
    rarity='legendary',
    age=11
)

Babka2 = fredde(
    name='Другая бабушка',
    color=[0, 0, 255],
    genid=-42,
    gendom=0.8,
    mutrate=0,
    rarity='mythic',
    age=11
)


baby, message = try_sex(Ded1, Babka1)
print(message)
baby2, message = try_sex(Ded2, Babka2)
print(message)


#if baby:
#    values = [
#        ("name", baby.name),
#        ("gender", baby.gender),
#        ("eyelashes", baby.eyelash),
#        ("age", baby.age),
#        ("generation", baby.generation),
#        ("genid", baby.genid),
#        ("gendom", baby.gendom),
#        ("mutrate", baby.mutrate),
#        ("color", baby.color)
#    ]
#
#    for name, value in values:
#        print(f"{name}: {value}")
#

step(freddies)
step(freddies)


baby3, message = try_sex(baby, baby2)
print(message)
baby4, message = try_sex(baby, baby2)
print(message)

step(freddies)
step(freddies)

baby5, message = try_sex(baby3, baby4)
print(message)
# print(baby.age)

#show_fredde(Babka1)

tree.show()
