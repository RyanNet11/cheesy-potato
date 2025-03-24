import os, subprocess, requests, time, random, sys, webbrowser, json
from datetime import datetime, timezone

# load config data
with open('config.json', 'r') as file:
    config = json.load(file)
    
username = config["AccountName"]
userid = config["userID"]
drive = config["Drive"]

gameRunning = False
eaRunning = False
restarts = 0
desiredServer = ""

# Classes
class initiate:
    def __init__(self, ip, guid, playercount="", battlelogdata="", gameID="",gameName=""):
        self.ip = ip
        self.GUID = guid
        self.playercount = playercount
        self.battlelogdata = battlelogdata
        self.gameID = gameID  
        self.gameName = gameName


class Servers:
    def __init__(self):
        self.RC1 = initiate("104.153.105.74:25200", "https://battlelog.battlefield.com/bf4/servers/show/pc/cfa68ec0-a030-4247-90e1-9b643a71edcd/?json=1&join=true")
        self.RC2 = initiate("192.223.30.251:25200", "https://battlelog.battlefield.com/bf4/servers/show/pc/8529e349-cd4a-4fa1-965a-afb4e8d7431e/?json=1&join=true")
        self.RC3 = initiate("74.91.119.140:25200", "https://battlelog.battlefield.com/bf4/servers/show/pc/de2e60c6-159a-4a5b-b30d-a1ee51998a8d/?json=1&join=true")
        self.idle = initiate("idle","idle","idle","idle","idle","idle")

class RestartException(Exception):
    pass

servers = Servers()
api_link = "https://api.bflist.io/bf4/v1/servers/"
battlelog_link = "https://battlelog.battlefield.com/bf4/servers/show/pc/cfa68ec0-a030-4247-90e1-9b643a71edcd/?json=1&join=true"
whereAt = ""
curent = ""

# Functions     
def updateAccountTracker():
    json =  {
            "Account": f"{username}",      
            "personaRef": f"{userid}",
            "inServer": f"{gameRunning}",
            "gameID": f"{desiredServer.gameID}",
            "timeSent": f"{datetime.now(timezone.utc)}"
        }        
    try:
        requests.put("https://accounting.rtx3080sc.workers.dev/", json=json)
    except:
        print("error sending account data to Ryan's tracker, please tell him")
       
def getData():
   
    for server_name in vars(servers):
        if server_name == "idle":  
            continue
        server = getattr(servers, server_name)  
        try:                                                                
            url =  server.GUID
            response = requests.get(url)
            response.raise_for_status()      

            data = response.json().get("data", {})                                  
            server.playercount = data["slots"]["2"].get("current", 0)
            server.gameID = data["gameId"]
            server.gameName = data["name"]
        except:
            print("Error getting data, trying again in 10 seconds")
            time.sleep(10)
            try:
                url =  server.GUID
                response = requests.get(url)
                response.raise_for_status()                
                data = response.json().get("data", {})                                  
                server.playercount = data["slots"]["2"].get("current", 0)
                server.gameID = data["gameId"]
                server.gameName = data["name"]
            except:
                print(f"Failed TWICE to retrieve data from {server}.")
                raise  RestartException
    #print("Data retrieval complete")

def findServer():
    time.sleep(1)
    global desiredServer
    try:
        if servers.RC1.playercount < 30:   
            print("RC1 has less than 30 players")
            desiredServer = servers.RC1
            return servers.RC1
        elif servers.RC3.playercount < 30:  
            print("RC3 has less than 30 players")
            desiredServer = servers.RC3
            return servers.RC3
        elif servers.RC2.playercount < 30:  
            print("RC2 has less than 30 players")
            desiredServer = servers.RC2
            return servers.RC2
        else:
            desiredServer = servers.idle
            print("No Servers need players")  
            return servers.idle
    except:
        print("Error finding server")
        raise  RestartException
   
def joinServer():
    joinGame = findServer()
    global gameRunning            
   
    if CheckIfGameRunning() == True:
        killGame()
        print("-- game tried to execute while already running an instance")   #game might say it launched when it already existed
        time.sleep(10)

    if CheckIfOriginIsRunning() == False:
        OpenOriginApp()
        print("EA app started")
        time.sleep(10)
       
    print("joining", f"{joinGame.gameName} with game ID ", joinGame.gameID)
    try:
        if os.path.exists(f'{drive}:\Program Files\EA Games\Battlefield 4'):
            subprocess.run(['start', '/min', 'bf4.exe', '-webMode', 'MP', '-Origin_NoAppFocus', '--activate-webhelper',
            '-requestState', 'State_ConnectToGameId', '-requestStateParams',
            f'<data  password="aarp" putinsquad="true" gameid="{joinGame.gameID}" role="soldier" personaref="{userid}" levelmode="mp"></data>', #os shenanigans here (fro's signature)
            '-Online.BlazeLogLevel', '2', '-Online.DirtysockLogLevel', '2' ],
            shell=True, cwd=f'{drive}:\Program Files\EA Games\Battlefield 4' )
        else:
            subprocess.run([ 'start', '/min', 'bf4.exe', '-webMode', 'MP', '-Origin_NoAppFocus', '--activate-webhelper',
            '-requestState', 'State_ConnectToGameId', '-requestStateParams',
            f'<data password="aarp" putinsquad="true" gameid="{joinGame.gameID}" role="soldier" personaref="{userid}" levelmode="mp"></data>',  #he used it cuz lots of VMs
            '-Online.BlazeLogLevel', '2', '-Online.DirtysockLogLevel', '2' ],
            shell=True, cwd=f'{drive}:\Program Files (x86)\Origin Games\Battlefield 4' )
        print("Game Launched, plaing", joinGame.gameName)
        gameRunning = True
    except:
        print("Error launching game, nuking all EA processes running")
        nukeEA()
        print("EA processes nuked, trying to launch game again")
        try:
            if os.path.exists(f'{drive}:\Program Files\EA Games\Battlefield 4'):
                subprocess.run(['start', '/min', 'bf4.exe', '-webMode', 'MP', '-Origin_NoAppFocus', '--activate-webhelper',
                '-requestState', 'State_ConnectToGameId', '-requestStateParams',
                f'<data  password="aarp" putinsquad="true" gameid="{joinGame.gameID}" role="soldier" personaref="{userid}" levelmode="mp"></data>', #os shananagains here (fro's signature)
                '-Online.BlazeLogLevel', '2', '-Online.DirtysockLogLevel', '2' ],
                shell=True, cwd=f'{drive}:\Program Files\EA Games\Battlefield 4' )
            else:
                subprocess.run([ 'start', '/min', 'bf4.exe', '-webMode', 'MP', '-Origin_NoAppFocus', '--activate-webhelper',
                '-requestState', 'State_ConnectToGameId', '-requestStateParams',
                f'<data password="aarp" putinsquad="true" gameid="{joinGame.gameID}" role="soldier" personaref="{userid}" levelmode="mp"></data>',  #he used it cuz lots of VMs
                '-Online.BlazeLogLevel', '2', '-Online.DirtysockLogLevel', '2' ],
                shell=True, cwd=f'{drive}:\Program Files (x86)\Origin Games\Battlefield 4' )
            print("Game Launched, playing", joinGame.gameName)
            gameRunning = True
        except:
            print("Error launching game a second time. Restarting")
            raise  RestartException
                     
def nukeEA():
   
    # This goes in and kills a long list of possible issues
    # caused by EA. We don't expect to kill everything, but
    # we will kill em all anyways just to be sure
    os.system("sc stop EABackgroundService >nul 2>&1 && echo [+] Successfully stopped EABackgroundService.")
    os.system("taskkill /F /IM EABackgroundService.exe >nul 2>&1 && echo [+] Successfully killed EABackgroundService.exe.")
    os.system("taskkill /F /IM EACefSubProcess.exe >nul 2>&1 && echo [+] Successfully killed EACefSubProcess.exe.")
    os.system("taskkill /F /IM EALocalHostSvc.exe >nul 2>&1 && echo [+] Successfully killed EALocalHostSvc.exe.")
    os.system("taskkill /F /IM ErrorReporter.exe >nul 2>&1 && echo [+] Successfully killed ErrorReporter.exe.")
    os.system("taskkill /F /IM Link2EA.exe >nul 2>&1 && echo [+] Successfully killed Link2EA.exe.")
    os.system("taskkill /F /IM EAConnect_microsoft.exe >nul 2>&1 && echo [+] Successfully killed EAConnect_microsoft.exe.")
    os.system("taskkill /F /IM EADesktop.exe >nul 2>&1 && echo [+] Successfully killed EADesktop.exe.")

def CheckIfGameRunning():
    #print("Checking if BF4 is running")
    time.sleep(1)
    global gameRunning
    headers = {
        "Host": "127.0.0.1:4219",
        "Origin": "https://battlelog.battlefield.com"    #need headers so it doesn't 404
    }
    try:
        response = requests.get("http://127.0.0.1:4219",headers=headers, timeout=9)   #should go through if game is running
        if response.status_code == 200:
            gameRunning = True
            #print(" - Game IS running")
            return True
    except:         #timeout means its just not responding. Consider it dead
        gameRunning = False
        #print(" - Game is NOT running")
        return False
       
def killGame():
    global gameRunning
    headers = {
        "Host": "127.0.0.1:4219",
        "Origin": "https://battlelog.battlefield.com"    #headers so it doesnt go kuflunk
    }
    try:
        response = requests.get("http://127.0.0.1:4219/killgame", headers=headers, timeout=1)
        if response.status_code == 200:
            print("Game Killed")                         #game is killed here
            gameRunning = False
    except requests.exceptions.ConnectionError:
        print("Error killing game")                       #just in case, id rather not go through lines of code
       
def CheckIfOriginIsRunning():
    #print("Checking if EA app is running")
    time.sleep(1)
    headers = {
        "Host": "127.0.0.1:4219",
        "Origin": "https://battlelog.battlefield.com"  
        #need headers so it doesnt 404
    }
    try:
        response = requests.get("http://127.0.0.1:3215/ping",headers=headers, timeout=9)      
        if response.json() == {'resp': 'pong'}:
            #print("EA app is Running")
            return True
    except:
        #print("EA app is not running")
        return False
       
def OpenOriginApp():                                        
    time.sleep(5)
    try:
        webbrowser.open('origin2://library/open?')
    except:
        print("error starting EA app - closing program")
        sys.exit()
       
    # let EA app perk up a little before next steps
    time.sleep(10)
       
def main():
    try:
        global gameRunning
        global curent
        global whereAt                           #these guys for keeping track of the cycles and destination
        cyclesSinceLastLaunch = 0


        CheckIfGameRunning()
        if gameRunning == True:   #kill the game here because we do not know what  
            killGame()
            time.sleep(10)         #server we are currently in
            if CheckIfGameRunning() == True:
                print("error exiting game")    
               
        if CheckIfOriginIsRunning() == False:
            OpenOriginApp()
            #print("waiting 15 seconds")       #make sure origin is up, who knows if its important
            time.sleep(15)
           
        while True:
            getData()
                   
            curent = whereAt                             #have a way to check new vs old whereabouts
            random_number = random.randint(20, 100)       #set a random number so we dont accidentally get funky data
            whereAt = findServer()                       # Store the returned value from find server


            if CheckIfGameRunning() == True:   #if true
                if whereAt.gameName == "idle":
                    print("servers are full, exiting game")
                    killGame()
                   
                elif whereAt != curent:
                    print(f"{curent.gameName}", "is full, joining", f"{whereAt.gameName}","instead")
                    killGame()
                    print("Waiting ", random_number, "seconds to join")
                    time.sleep(random_number)
                    joinServer()
                   
                elif whereAt == curent:
                    print("Staying in ", whereAt.gameName)
            else:
                if whereAt.gameName == "idle":
                    print("Servers are full, staying idle")
                   
                elif whereAt != curent:
                    print(f"{whereAt.gameName}", " needs players, joining now")
                    print("Waiting ", random_number, "seconds to join")
                    time.sleep(random_number)
                    joinServer()
                   
                elif whereAt == curent:
                    print("Server did not change, but game is not running")
                    print("Assume game crashed, attempting rejoin")
                    print("Waiting ", random_number, "seconds to join")
                    time.sleep(random_number)
                    joinServer()
                   
                else:
                    print("  - Error: Game is not running, no parameters met -  ")
                    print(servers)
            updateAccountTracker()
            print("sleeping for 10 minutes")
            time.sleep(600)
    except RestartException:
        print("Error in main loop, restarting")
        main()
    except KeyboardInterrupt:
        print("Keyboard Interrupt, exiting")
        sys.exit()


main()





