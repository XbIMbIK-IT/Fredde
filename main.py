from fredde import freddies
from fredde import Fredde
from sex import try_sex,sex
import tree
from simulation import step
from freddePhoto import show_fredde
from freddePhoto import save_fredde

Ded1 = Fredde(
    name='Гипнокрад',
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

Babka1 = Fredde(
    name='Агафья',
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

Ded2 = Fredde(
    name='Касеки',
    eyelash=False,
    eye='ghoul',
    hatAcs='horns2',
    faceAcs='drop',
    bodyPattern='xeno',
    color=[131, 71, 201],
    genid=20,
    gendom=0.8,
    mutrate=0,
    rarity='common',
    age=11
)

Babka2 = Fredde(
    name='Бабка гренни',
    eyelash=False,
    eye='herobrine',
    hatAcs='nimbus',
    faceAcs='tears',
    bodyPattern='blood',
    color=[14, 12, 224],
    genid=20,
    gendom=0.8,
    mutrate=0,
    rarity='common',
    age=11
)

Ded3 = Fredde(
    name='Хрящ',
    eyelash=False,
    eye='ghoul',
    hatAcs='horns2',
    faceAcs='drop',
    bodyPattern='xeno',
    color=[12, 71, 44],
    genid=20,
    gendom=0.8,
    mutrate=0,
    rarity='common',
    age=11
)

Babka3 = Fredde(
    name='Баба капа',
    eyelash=False,
    eye='herobrine',
    hatAcs='nimbus',
    faceAcs='tears',
    bodyPattern='blood',
    color=[131, 12, 12],
    genid=20,
    gendom=0.8,
    mutrate=0,
    rarity='common',
    age=11
)

Gurin = Fredde(
    name='Гурин',
    eyelash=False,
    eye='gurin',
    hatAcs='gurin',
    eyeAcs='gurin',
    faceAcs='gurin',
    bodyPattern='afghanistan',
    color=[255, 255, 255],
    genid=20,
    gendom=0.8,
    mutrate=0,
    rarity='common',
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


baby3, message = try_sex(Ded3, Babka3)
print(message)
step(freddies)
step(freddies)

baby4, message = try_sex(baby, baby2)
step(freddies)
step(freddies)
baby5, message = try_sex(baby3, baby4)
baby6, message = try_sex(baby4, Ded3)
step(freddies)
step(freddies)
baby7, message = try_sex(baby3, baby5)
# print(baby.age)

#show_fredde(Babka1)

tree.main()
