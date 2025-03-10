import os, subprocess, requests, time, random, logging, sys, builtins
from datetime import datetime

userid = "1938903914"
gameRunning = False
eaRunning = False
servers = {    #set up a place for all the data to live happily ever after
    "RC1": {
        "ip": "104.153.105.74:25200",
        "GUID":"",
        "api_data": "",
        "battlelog_data":"",
        "player_count": ".",
        "gameID":""
    },
    "RC2": {
        "ip": "192.223.30.251:25200",
        "GUID":"",
        "api_data": "",
        "battlelog_data":"",
        "player_count": "",           
        "gameID":""
    },
    "RC3": {
        "ip": "74.91.119.140:25200",
        "GUID":"",
        "api_data": "",
        "battlelog_data":"",
        "player_count": "",
        "gameID":""
    }
}

api_link = "https://api.bflist.io/bf4/v1/servers/"

battlelog_link = "https://keeper.battlelog.com/snapshot/"
whereAt = ""
curent = ""

log_filename = f"log_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(log_filename),  # Save logs to file
        logging.StreamHandler(sys.stdout)   # Print logs to console
    ]
)
def print_with_log(*args, **kwargs):
    message = " ".join(str(arg) for arg in args)
    logging.info(message)
builtins.print = print_with_log

def API_data():
    for server_name, server_info in servers.items():     #get data from api for players and GUID
        url = api_link + server_info["ip"]
        response = requests.get(url)
        servers[server_name]["api_data"] = response.json()
        if response.status_code != 200:
            print(f"Error API: {response.status_code}")
    print("-- API Data Received")
    for server_name, server_info in servers.items():   # set player coutns and GUID in the servers list
        server_info["player_count"] = server_info["api_data"].get("numPlayers", 0) 
        server_info["GUID"] = server_info["api_data"].get("guid", 0) 
        # print(server_info["player_count"])  
        # print(server_info["GUID"]) 
    print("-- API Data Processed")
            
def Battlelog_data():
    for server_name, server_info in servers.items():    #battlelog data based off api guid
        url = battlelog_link + server_info["GUID"]
        response = requests.get(url)
        servers[server_name]["battlelog_data"] = response.json()
        if response.status_code != 200:
            print(f"Error Battlelog: {response.status_code}")
    print("-- Battlelog Data Received")
    for server_name, server_info in servers.items():
        server_info["gameID"] = server_info["battlelog_data"]["snapshot"].get("gameId")
    print("-- Battlelog Data Processed")

def findServer():
    print("Finding Server to join")
    if servers["RC1"]["player_count"] < 30:    # seed RC1 first
        print("RC1 has less than 30 players")
        return "RC1"
    elif servers["RC3"]["player_count"] < 30:  # seed RC3 next
        print("RC3 has less than 30 players")
        return "RC3"
    elif servers["RC2"]["player_count"] < 30:  # seed RC2 last
        print("RC2 has less than 30 players")
        return "RC2"
    else:
        print("No Servers need players")        #go nowhere
        return "idle"
    
def joinServer():
    server = findServer()
    if CheckIfGameRunning() == True:
        killGame()
        print("-- game tried to exicute while already running an instance")   #game might say it launched when it already existed
        time.sleep(10)
        
    print("joining", f"{server}")
    
    gameID = servers[f"{server}"]["gameID"]
    if os.path.exists('C:\Program Files\EA Games\Battlefield 4'):
        subprocess.run([ 'bf4.exe', '-webMode', 'MP', '-Origin_NoAppFocus', '--activate-webhelper', 
           '-requestState', 'State_ConnectToGameId', '-requestStateParams', 
           f'<data  password="aarp" putinsquad="true" gameid="{gameID}" role="soldier" personaref="{userid}" levelmode="mp"></data>', #os shananagains here (fro's signature)
           '-Online.BlazeLogLevel', '2', '-Online.DirtysockLogLevel', '2' ], 
           shell=True, cwd='C:\Program Files\EA Games\Battlefield 4' )
    else:
        subprocess.run([ 'bf4.exe', '-webMode', 'MP', '-Origin_NoAppFocus', '--activate-webhelper',
           '-requestState', 'State_ConnectToGameId', '-requestStateParams',
           f'<data password="aarp" putinsquad="true" gameid="{gameID}" role="soldier" personaref="{userid}" levelmode="mp"></data>',  #he used it cuz lots of VMs
           '-Online.BlazeLogLevel', '2', '-Online.DirtysockLogLevel', '2' ],
           shell=True, cwd='C:\Program Files (x86)\Origin Games\Battlefield 4' )
    print("Game Exicuted")

def CheckIfGameRunning():
    print("Checking if BF4 is running")
    global gameRunning
    headers = {
        "Host": "127.0.0.1:4219",
        "Origin": "https://battlelog.battlefield.com"    #need headers so it doesnt 404
    }
    try:
        response = requests.get("http://127.0.0.1:4219",headers=headers, timeout=9)   #should go through if game is running
        if response.status_code == 200:
            gameRunning = True
            print(" - Game IS running")
            return True
    except requests.exceptions.Timeout:         #timeout means its just not responding. Consider it dead
        gameRunning = False
        print(" - Game is NOT running")
        return False
    except requests.exceptions.RequestException:  # if its not running it will error, this catchas that
        gameRunning = False
        print("- Game is NOT running")
        return False
        
def killGame():
    headers = {
        "Host": "127.0.0.1:4219",
        "Origin": "https://battlelog.battlefield.com"    #headers so it doesnt go kuflunk
    }
    try:
        response = requests.get("http://127.0.0.1:4219/killgame", headers=headers, timeout=1)
        if response.status_code == 200:
            print("Game Killed")                         #game is killed here
            gameActive = False
    except requests.exceptions.ConnectionError:
        print("Error killing game")                       #just in case, id rather not go through lines of code 
        
def CheckIfOriginIsRunning():
    print("Checking if EA app is running")
    try:
        response = requests.get("http://127.0.0.1:3215/ping", timeout=9)       #not really sure if ill use this, but i have it
        eaRunning = True
        print("ea app running?", f"{eaRunning}")                               #if one day I need it
    except requests.exceptions.Timeout:
        eaRunning = False
        print("ea app running?", f"{eaRunning}")
    except requests.exceptions.RequestException:  
        eaRunning = False
        print("ea app running?", f"{eaRunning}")
        
def OpenOriginApp():                                          #same thing here, dont think I need this but Whatever
    try:
        subprocess.run([r"C:\Program Files\Electronic Arts\EA Desktop\EA Desktop\EALauncher.exe"], check=True)
        print("EA Launcher started successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error launching EA Launcher: {e}")
    except FileNotFoundError:
        print("EALauncher.exe not found. Please check the path.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        
def main():
    #first exicution means we need to populate the data and make sure 
    #that the user added the userID of the account being used
    if userid == "":
        print("Please add your user ID to the script")
        return
    
    global curent
    global whereAt                           #these guys for keeping track of the cycles and destination
    cyclesSinceLastLaunch = 0

    CheckIfGameRunning()
    if gameRunning == True:   #kill the game here because we dont know what  
        killGame()
        time.sleep(10)         #server we are curently in
        if CheckIfOriginIsRunning() == True:
            print("error exiting game")    
            
    if CheckIfOriginIsRunning() == False:
        OpenOriginApp()
        print("waiting 15 seconds")       #make sure origin is up, who knows if its important
        time.sleep(15)
        
    while True:
        API_data()        #get the data
        Battlelog_data()  #and more data
        
        curent = whereAt                             #have a way to check new vs old wherabouts
        random_number = random.randint(20, 100)       #set a random number so we dont accidently get funky data
        whereAt = findServer()                       # Store the returned value from findServer

        if CheckIfGameRunning() == True:   #if true
            if whereAt == "idle":
                print("servers are full, exiting game")
                killGame()
            elif whereAt != curent:
                print(f"{curent}", "is full, joining", f"{whereAt}","instead")
                killGame()
                print("RandOmIzIng TIminG ActIoNs fOr FunNy ReaASonz")
                time.sleep(random_number)
                joinServer()
            elif whereAt == curent:
                print("Staying put")
            else:
                print("  - Something went wrong, game is running but nothing works!!  - ")
                print(servers)
        else:
            if whereAt == "idle":
                print("Servers are full, staying put")
            elif whereAt != curent:
                print(f"{whereAt}", " needs players, joining now")
                print("RandOmIzIng TIminG ActIoNs fOr FunNy ReaASonz")
                time.sleep(random_number)
                joinServer()
            elif whereAt == curent:
                print("Server did not change, but game is not running")
                print("Assume game crashed, attempting rejoin")
                print("RandOmIzIng TIminG ActIoNs fOr FunNy ReaASonz")
                time.sleep(random_number)
                joinServer()
            else:
                print("  - Error: Game is not running, no paramiters met -  ")
                print(servers)
        time.sleep(100)
        
        
            
main()

    
# if CheckIfGameRunning() == False and whereAt != "idle":   #assume server crashes and join again
#             print("game is gone, joining",f"{whereAt}")
#             print("waiting ",f"{random_number}"," seconds")
#             time.sleep(random_number)
#             joinServer()
#             cyclesSinceLastLaunch = 1
            
#         if whereAt == "idle":                     # dont join server if servers are full
#             if CheckIfGameRunning() == True:
#                 print("servers are full, quitting now")
#                 cyclesSinceLastLaunch = 1

#             else:
#                 print("Servers full, staying put")
#                 cyclesSinceLastLaunch += 1
#         elif curent != whereAt:                    #if new destination is different from current, switch
#             if CheckIfGameRunning == True:
#                 killGame()
#                 print("waiting ",f"{random_number}"," seconds")
#                 time.sleep(random_number)
#                 joinServer()
#                 cyclesSinceLastLaunch = 1
#             else:
#                 print("Game exited unexpectidly. Reattempting join")
#                 print("waiting ",f"{random_number}"," seconds")
#                 time.sleep(random_number)
#                 joinServer()
#                 cyclesSinceLastLaunch = 1
#         else:                                      #if nothing happens, then were good to just stay put
#             cyclesSinceLastLaunch += 1  
#         print("Game State Stable. Waiting 5 minutes. Cycle counter =",f"{cyclesSinceLastLaunch}")
#         time.sleep(300)