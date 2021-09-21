from rcon import Client
import os
import uuid
import time
import subprocess
import psutil

def nav_generate(mapName, gameExe, gameDir, hijack, textmode):

    logName = mapName + "_nav.log";
    logPath = os.path.join(gameDir, logName)
    passwd = str(uuid.uuid4())

    def pre_flight():
        # check if client is already open,
        # check if it is fit for hijack,
        # otherwise terminate process
        process_name = gameExe.split('\\')[-1]
        p = next((p for p in psutil.process_iter() if p.name() == process_name), None)
        if p and '-usercon' in p.cmdline():
            return True
        elif p:
            p.terminate()
        return False

    highjackable = pre_flight()

    def cleanup_log(client):
        client.run("con_logfile", '""')
        if os.path.exists(logPath):
            os.remove(logPath)

    def wait_for_rcon():
        print('Waiting for RCON...', end='')
        while True:
            try:
                time.sleep(3)
                with Client("127.0.0.1", 27015, passwd=passwd) as client:
                    break
            except:
                print('.', end='')
                # was your game client launched with -usercon?

    def wait_for_log_exists():
        while not os.path.exists(logPath):
            time.sleep(1)

    def wait_for_nav_completion():
        f = open(logPath, 'r')
        while not [True for line in f.readlines() if ".nav' saved." in line]:
            time.sleep(1)
        f.close()

    launch_params = [
        gameExe, '-game', gameDir, '-windowed', '-novid', '-nosound',
        '-usercon', '+ip', '0.0.0.0', '+rcon_password', passwd, 
        '+log', '0', '+sv_logflush', '1', '+map', mapName]
    hijack and highjackable and launch_params.append('-hijack')
    textmode and launch_params.append('-textmode')
    subprocess.Popen(launch_params,
            creationflags=subprocess.DETACHED_PROCESS | 
            subprocess.CREATE_NEW_PROCESS_GROUP)

    wait_for_rcon()

    with Client("127.0.0.1", 27015, passwd=passwd) as client:
        print('\nGenerating Navigation Mesh...')
        cleanup_log(client)
        client.run("con_logfile", logName)
        client.run("nav_generate")
        wait_for_log_exists()
        wait_for_nav_completion()
        cleanup_log(client)
        if hijack:
            client.run("disconnect")
        else:
            client.run("quit")
