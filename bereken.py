def bereken(startinleg, maandinleg, rente, looptijd):
    for i in range(12*int(looptijd)):
        startinleg = startinleg + (maandinleg + (startinleg * (((365./12.)/365.) * rente)))
        print str(startinleg) + "\n"
    return startinleg
    
print bereken(25., 25., .019, 14.)