#   Update GOG Collection
# 
#  Tasks:
#  - Compare GOG FTP to Local Copy (rclone)
#  - get new/updated games
#  - download them
#  - archive them (format: gamename (dd-MM-yy) and add comment
#  - copy them to 1fichier gog dir
#  - delete older existing games (on 1fichier cloud)
# 

from datetime import datetime
import os, re, shutil, subprocess, sys
currentDir = os.getcwd()
gamesPassed = []

log = list()
log.append("\n")

def writeLogToFile(logVar, path, filename):
    f = open(path+filename, 'a', encoding='utf8')
    f.writelines(logVar)
    f.close()

def logMessage(message):
    fullMsg = "[{}] {}\n".format(datetime.now().strftime("%d/%m/%Y %H:%M:%S"), message)
    print(fullMsg)
    log.append(fullMsg)

def getNewUpdatedGames():
    cmd = "rclone sync gog-games: E:\GOG_VERIFIED --size-only --sftp-disable-hashcheck --dry-run -P"
    proc = subprocess.Popen(cmd, shell=True, stdout = subprocess.PIPE,)
    lst = proc.communicate()[0].decode("utf8").strip().split("\n")
    result = set([ re.search(r'NOTICE: (.*?)/', game).group(1) for game in lst if "NOTICE:" in game and "/" in game])
    logMessage("New/updated games: {}".format(len(result)))
    logMessage(str(result))
    return result

def updateGamesLocal():
    cmd = "rclone sync gog-games: E:\GOG_VERIFIED --size-only --sftp-disable-hashcheck --transfers=2 -P"
    logMessage("Syncing local copy with FTP ...")
    os.system(cmd)

def moveToCheckQueue(games):
    logMessage("Moving games to verification queue ...")
    for game in games:
        src = "E:\\GOG_VERIFIED\\{}".format(game)
        dst = "E:\\VERIFICATION_QUEUE\\{}".format(game)
        logMessage("Moving {} from {} to {} ...".format(game, src, dst))
        shutil.move(src, dst)

def checkFile(file):
    # cmd = "bash ggchk -s \"{}\"".format(file) # ORIGINAL
    cmd = "bash ggchk \"{}\"".format(file)
    proc = subprocess.Popen(cmd, shell=True, stdout = subprocess.PIPE,)
    return proc.communicate()[0].decode("utf8").strip()

def integrityCheck(game):
    logMessage("Checking game files for authenticity ... ({})".format(game.split("\\")[2]))
    
    os.chdir(game)
    status = dict()
    # Only check .exe and .bin files, don't check others
    for f in os.listdir():
        if any ( [".exe" in f, ".bin" in f]):
            fileStatus = checkFile(f)
            status[f] = fileStatus
            #log.append(fileStatus)
            # log.append("[{}] {}".format(datetime.now().strftime("%d/%m/%Y %H:%M:%S"), fileStatus))
            logMessage(fileStatus)
            if not fileStatus.endswith("OK"):   
                # os.chdir(currentDir)
                logMessage("Integrity check failed. Folder skipped.")
                os.chdir(currentDir)
                return False
    os.chdir(currentDir)
    return all(g.endswith("OK") for g in status.values())

def moveIfCheckPassed(game):
    verifiedPath = "E:\\GOG_VERIFIED\\"
    # MAKE SURE TO RUN THE SCRIPT FROM GOG DIR WHERE "CHECKLIST" AND "VERIFIED" ARE LOCATED
    if integrityCheck(game):
        gameName = game.split("\\")[-1]
        logMessage("Integrity check passed! Moving {} to {}".format(gameName, verifiedPath))
        gamesPassed.append(gameName)
        shutil.move(game, verifiedPath+gameName)

def moveGamesBackIfVerificationPassed():
    verification_dir = "E:\\VERIFICATION_QUEUE\\"
    for game in os.listdir(verification_dir):
        moveIfCheckPassed(verification_dir + game)

def packGamesForUpload(updatedGames):
    scriptDir = "E:\\SCRIPT\\"
    messageFile = "message.txt"
    uploadPath = "D:\\GOG_UPLOAD\\"
    gamePath = "E:\\GOG_VERIFIED\\"
    currentDate = datetime.now().strftime("%d-%m-%y")
    gogVersionPattern = r'\(([^()]+)\)\.exe$'
    syntax = 'rar a -m0 -z{} -ep1 "{}{}{} ({}).rar" "{}{}"'
    logMessage("Changed working directory to: {}".format(scriptDir))
    os.chdir(scriptDir)
    logMessage("Creating RAR archives ...")
    count = 1
    for game in updatedGames:
        gameContents = [f for f in os.listdir(gamePath+game) if f.endswith(".exe") and "(" in f]
        if len(gameContents) > 0:
            match = re.search(gogVersionPattern, gameContents[0])
        else:
            match = False
        gogVersion = ""
        if match:
            gogVersion = " ({})".format(match.group(1))
        rarScript =  syntax.format(messageFile, uploadPath, game, gogVersion, currentDate, gamePath, game)
        logMessage("Creating RAR archive for {} ... (Progress: {}/{})".format(game, count, len(updatedGames)))
        os.system(rarScript)
        count += 1
        
def deleteExistingfrom1fichier():
    uploadQueue = [game.split(" ")[0] for game in os.listdir("D:\\GOG_UPLOAD")]
    _1fCloud = {}
    
    cmd = "rclone lsf 1f:/GOG"
    proc = subprocess.Popen(cmd, shell=True, stdout = subprocess.PIPE,).communicate()[0].decode("utf8").strip().split("\n")
    for g in proc:
        _1fCloud[g.split(" ")[0]] = g
    
    for g in uploadQueue:
        if g in _1fCloud:
            logMessage("Deleting {} from 1fichier cloud ...".format(_1fCloud[g]))
            os.remove("X:/{}".format(_1fCloud[g]))
            # os.system("rclone delete \"{}{}\"".format(_1fCloudPath, _1fCloud[g]))

def cleanupUploadFolder():
    uploadDir = "D:\\GOG_UPLOAD\\"
    for f in os.listdir(uploadDir):
        os.remove(uploadDir+f)


def generateGOGContents():
    currentDate = datetime.now().strftime("%d-%m-%y")

    script_header = """GOG Games Complete Collection (PC, Windows, ENG)
    Updated as of {}

- Executables + BIN files are all checked for authenticity

    """
    script = []
    games = os.listdir("E:\\GOG_VERIFIED")

    for g in games:
        script.append("\n")
        contents = os.listdir("E:\\GOG_VERIFIED\\{}".format(g))
        contentsDict = dict()
        contentsDict["files"] = []
        contentsDict["goodies"] = []
        for f in contents:
            if f.endswith(".exe") or f.endswith(".bin"):
                contentsDict["files"].append(f)
            else:
                contentsDict["goodies"].append(f)

        prefix = "|---> {}\n"
        script.append("slug: {}\n\n".format(g))
        script.append("Game + DLC: \n")
        for f in contentsDict["files"]:
            script.append(prefix.format(f))

        if len(contentsDict["goodies"]) > 0:
            script.append("\nGoodies: \n")
            for f in contentsDict["goodies"]:
                script.append(prefix.format(f))
        script.append("\n\n")

    gog_contents = open("{}\\gog_contents.txt".format(sys.path[0]),'w')
    gog_contents.write(script_header.format(currentDate))
    gog_contents.writelines(script)
    gog_contents.close()

def updateGit():
    addCmd = "git add ."
    commitCmd = "git commit -m \"{}\"".format(datetime.now().strftime("%d-%m-%y"))
    pushCmd = "git push origin main"
    logMessage("Updating text file on gitHub ...")
    for cmd in [addCmd, commitCmd, pushCmd]:
        os.system(cmd)

def run():
    print("What do you want to do? CHOICES: \n 1- Update, Sync and Delete (WITH LOG FILE)")
    print(" 2- Delete older files from cloud (Make sure 1fichier gog folder is mounted (1f:/GOG) and new files are in gog_upload folder, use this before uploading new/updated games to cloud)")
    print(" 3- Cleanup upload folder")
    print(" 4- Generate GOG Contents (txt file) and push changes to repo")
    print("Type any other number to exit:")

    choice = int(input())

    if choice == 1:
        updated_new_games = getNewUpdatedGames()        # Get new/updated games (WORKS)
        updateGamesLocal()                              # Sync ftp to local (Download/Remove) (WORKS)
        moveToCheckQueue(updated_new_games)             # Move games to check queue
        moveGamesBackIfVerificationPassed()             # Check game files for authenticity, then move them back to gog root dir (WORKS)
        packGamesForUpload(gamesPassed)            # Create RAR files for upload
        writeLogToFile(log, "D:\\", "gog_games_log.txt") # Write log to file

    elif choice == 2:
        deleteExistingfrom1fichier()
        writeLogToFile(log, "D:\\", "gog_games_log.txt")

    elif choice == 3:
        cleanupUploadFolder()

    elif choice == 4:
        generateGOGContents()
        updateGit()
        writeLogToFile(log, "D:\\", "gog_games_log.txt")

    else:
        exit()

# print(len(updated_new_games))

# updateGamesLocal()
# moveToCheckQueue(updated_new_games)
# moveGamesBackIfVerificationPassed()

# os.chdir("E:\\VERIFICATION_QUEUE")


#ENABLE ALL FOR NEWER GAMES
# updated_new_games = getNewUpdatedGames()        # Get new/updated games (WORKS)
# updateGamesLocal()                              # Sync ftp to local (Download/Remove) (WORKS)
# moveToCheckQueue(updated_new_games)             # Move games to check queue


# RUN THIS TOMORROW, ENABLE OTHER 3 ABOVE AFTER SCRIPT SUCCESSFULLY EXECUTES.

# moveGamesBackIfVerificationPassed()             # Check game files for authenticity, then move them back to gog root dir (WORKS)
# packGamesForUpload(gamesPassed)            # Create RAR files for upload
# writeLogToFile(log, "D:\\", "gog_games_log.txt") # Write log to file

run()