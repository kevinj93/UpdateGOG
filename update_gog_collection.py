#   Update GOG Collection
# 
#  Tasks:
#  - Compare GOG FTP to Local Copy (rclone)
#  - get new/updated games
#  - download them
#  - archive them (format: gamename (dd-MM-yy) and add comment
#  - copy them to 1fichier gog dir
#  - delete older existing games
# 
# 
# 
# 
# 

import datetime, os, re, shutil, subprocess

log = list()


def getNewUpdatedGames():
    cmd = "rclone sync gog-games: E:\GOG_VERIFIED --size-only --sftp-disable-hashcheck --dry-run -P"
    proc = subprocess.Popen(cmd, shell=True, stdout = subprocess.PIPE,)
    lst = proc.communicate()[0].decode("utf8").strip().split("\n")
    return set([ re.search(r'NOTICE: (.*?)/', game).group(1) for game in lst if "NOTICE:" in game and "/" in game])

def updateGamesLocal():
    cmd = "rclone sync gog-games: E:\GOG_VERIFIED --size-only --sftp-disable-hashcheck -P"
    os.system(cmd)

def moveToCheckQueue(games):
    for game in games:
        shutil.move("E:\\GOG_VERIFIED\\{}".format(game), "E:\\VERIFICATION_QUEUE\\{}".format(game))

def checkFile(file):
    # cmd = "bash ggchk -s \"{}\"".format(file) # ORIGINAL
    cmd = "bash ggchk \"{}\"".format(file)
    proc = subprocess.Popen(cmd, shell=True, stdout = subprocess.PIPE,)
    return proc.communicate()[0].decode("utf8").strip()

def integrityCheck(dr):
    
    status = dict()
    # Only check .exe and .bin files, don't check others
    for f in os.listdir(dr):
        if any ( [".exe" in f, ".bin" in f]):
            fileStatus = checkFile(dr + "/" + f)
            status[f] = fileStatus
            #log.append(fileStatus)
            log.append("[{}] {}".format(datetime.now().strftime("%d/%m/%Y %H:%M:%S"), fileStatus))
            if not fileStatus.endswith("OK"):
                log.append("[{}] Integrity check failed. Folder skipped.".format(datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
                return False

def moveIfCheckPassed(game):
    # MAKE SURE TO RUN THE SCRIPT FROM GOG DIR WHERE "CHECKLIST" AND "VERIFIED" ARE LOCATED
    if integrityCheck(game):
        shutil.move(game, "E:\\GOG_VERIFIED\\"+game)

def moveGamesBack():
    verification_dir = "E:\\VERIFICATION_QUEUE\\"
    for game in os.listdir(verification_dir):
        moveIfCheckPassed(verification_dir + game)


updated_new_games = getNewUpdatedGames()
updateGamesLocal()
moveToCheckQueue(updated_new_games)
moveGamesBack()

# os.chdir("E:\\VERIFICATION_QUEUE")



