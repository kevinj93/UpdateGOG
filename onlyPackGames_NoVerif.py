from datetime import datetime
import os, re

currentDir = os.getcwd()

log = list()
log.append("\n")

def packGamesForUpload(updatedGames):
    scriptDir = "E:\\SCRIPT\\"
    messageFile = "message.txt"
    uploadPath = "D:\\GOG_UPLOAD\\"
    gamePath = "E:\\VERIFICATION_QUEUE\\"
    currentDate = datetime.now().strftime("%d-%m-%y")
    gogVersionPattern = r'\(([^()]+)\)\.exe$'
    syntax = 'rar a -m0 -z{} -ep1 "{}{}{} ({}) _.rar" "{}{}"'
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

def logMessage(message):
    fullMsg = "[{}] {}\n".format(datetime.now().strftime("%d/%m/%Y %H:%M:%S"), message)
    print(fullMsg)
    log.append(fullMsg)

def writeLogToFile(logVar, path, filename):
    f = open(path+filename, 'a', encoding='utf8')
    f.writelines(logVar)
    f.close()

#packGamesForUpload(os.listdir("E:\\VERIFICATION_QUEUE\\"))
#writeLogToFile(log, "D:\\", "gog_games_log.txt")

def filesToDelete():
    
    ul_dir_files = os.listdir("D:\\GOG_UPLOAD")
    slugs = [g.split(" ")[0] for g in ul_dir_files]
    cloud_dir_files = os.listdir("X:\\")
    cloud_dir_dict = dict()

    for f in cloud_dir_files:
        cloud_dir_dict[f.split(" ")[0]] = f

    return [cloud_dir_dict[key] for key in cloud_dir_dict if key in slugs]


count = 1
total = len(filesToDelete())

for f in filesToDelete():
    
    print("deleting {} ({}/{})...".format(f, count, total))
    os.remove("X:\\{}".format(f))
    count += 1