from valveexe import ValveExe
from totcommon.logger import stdout

def nav_generate(mapName, gameExe, gameDir, steamExe, steamId):
    valveExe = ValveExe(gameExe, gameDir, steamExe, steamId)
    stdout('Launching game...')

    valveExe.launch(['-windowed', '-novid', '-nosound', 
                     '+sv_cheats', '1', '+map', mapName])
    stdout('Waiting for map load...')

    valveExe.logger.log_until('Redownloading all lightmaps|connected\.')

    with valveExe as console:
        stdout('Generating Navigation Mesh...')

        console.run("nav_generate")
        valveExe.logger.log_until("\.nav' saved\.")

        if (valveExe.hijacked):
            console.run("disconnect")
        else:
            console.run("quit")

    del valveExe

    stdout('Generation complete!')