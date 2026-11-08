import os
import re
import time
from shutil import copyfile
from valveexe import ValveExe, EXEC
from totcommon.logger import stdout


# How long the game may go without writing a single console line before we
# assume it is wedged. Map loading and nav generation both report progress
# as they go, so silence this long means a crash dialog or a hang.
IDLE_TIMEOUT = 300

LAUNCH_PARAMS = ['-windowed', '-novid', '-nosound', '+sv_cheats', '1']


class GameLostError(RuntimeError):
    '''Raised when the game dies or stops responding before the console
    output we were waiting for ever shows up.'''


def _log_until(valveExe, until, doing, idle_timeout=IDLE_TIMEOUT):
    '''A :any:`log_until<valveexe.logger.Logger.log_until>` that gives up.

    ValveEXE's own version polls forever, so a game that crashes mid-command
    leaves AutoNav waiting silently. Give up once the game process is gone,
    or once the log has gone `idle_timeout` seconds without output.
    '''
    logs = ''
    last_output = time.time()

    while not re.search(until, logs):
        time.sleep(0.5)

        fresh = valveExe.logger.log_ingest()
        if fresh:
            logs += fresh
            last_output = time.time()
            continue

        # Only judged once the log is drained, so a crash's final lines are
        # ingested before we decide the game is gone.
        if valveExe._our_process() is None:
            raise GameLostError('The game closed while {}.'.format(doing))

        if time.time() - last_output > idle_timeout:
            raise GameLostError(
                'The game stopped responding while {} '
                '(no console output for {}s).'.format(doing, idle_timeout))

    return logs


def _keep_log(valveExe):
    '''Copies the console log out of the way, since ValveEXE's cleanup
    deletes the original -- and with it the only record of a failure.'''
    if not valveExe.logPath:
        return None
    kept = os.path.join(valveExe.gameDir,
                        'autonav-crash-' + valveExe.uuid + '.log')
    try:
        copyfile(valveExe.logPath, kept)
    except OSError:
        return None
    return kept


def _run(console, command, *params):
    '''Issues a console command, tolerating the connection dying underneath it.

    RconConsole blocks on the socket until the game answers, so a game that
    crashes mid-command surfaces as a raw socket error. The console log is the
    real source of truth for whether the command ran, so swallow the transport
    failure here and let the caller's wait decide what happened.
    '''
    try:
        console.run(command, *params)
    except (ConnectionError, TimeoutError) as e:
        stdout('Lost the console connection running "{}" ({}).'.format(
            command, e.__class__.__name__))


def nav_generate(mapName, gameExe, gameDir, steamExe, steamId, console=EXEC):
    valveExe = ValveExe(gameExe, gameDir, steamExe, steamId, console)
    try:
        stdout('Launching game...')
        valveExe.launch(LAUNCH_PARAMS + ['+map', mapName])

        with valveExe as console:
            # Waited on for every console type: the log is the only reliable
            # sign the map is in, rcon or not.
            stdout('Waiting for map load...')
            _log_until(valveExe, r'Redownloading all lightmaps|connected\.',
                       'loading the map')

            stdout('Generating Navigation Mesh...')
            _run(console, 'nav_generate')
            _log_until(valveExe, r"\.nav' saved\.", 'generating the nav mesh')

            time.sleep(1)

            if valveExe.hijacked:
                _run(console, 'disconnect')

    except BaseException:
        kept = _keep_log(valveExe)
        if kept:
            stdout('Console log kept at: ' + kept)
        raise

    finally:
        # Hands the game and the game folder back the way we found them:
        # console closed, con_logfile reset on a hijacked game, our log and
        # cfg removed, and a game we launched closed with a graceful `quit`
        # (a killed game leaves Steam holding a stale UserID ticket). Runs on
        # failure too, so a crashed run doesn't leave the game behind.
        valveExe.cleanup()

    stdout('Generation complete!')
