import time
from valveexe import ValveExe
from valveexe.console import RconConsole
from totcommon.logger import stdout


def nav_generate(mapName, gameExe, gameDir, steamExe, steamId):
    valveExe = ValveExe(gameExe, gameDir, steamExe, steamId)
    stdout('Launching game...')
    valveExe.launch(['-windowed', '-novid', '-nosound',
                     '+sv_cheats', '1', '+map', mapName])

    with valveExe as console:
        if not isinstance(console, RconConsole):
            stdout('Waiting for map load...')
            map_loaded = 'Redownloading all lightmaps|connected\.'
            valveExe.logger.log_until(map_loaded)

        stdout('Generating Navigation Mesh...')

        console.run("nav_generate")
        valveExe.logger.log_until("\.nav' saved\.")

        time.sleep(1)

        if valveExe.hijacked:
            console.run("disconnect")
        
    if not valveExe.hijacked:
        valveExe.quit()

    del valveExe

    stdout('Generation complete!')
