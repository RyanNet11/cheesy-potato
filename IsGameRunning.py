import requests
def CheckIfGameRunning():
    print("Checking if BF4 is running")
    headers = {
        "Host": "127.0.0.1:4219",
        "Origin": "https://battlelog.battlefield.com"
    }
    try:
        response = requests.get("http://127.0.0.1:4219",headers=headers, timeout=9)
        if response.status_code == 200:
            gameRunning = True
            print("Game IS running")
    except requests.exceptions.Timeout:
        gameRunning = False
        print("Game is NOT running")
    except requests.exceptions.RequestException:  # Catches other errors like connection errors
        gameRunning = True
        print("Game is NOT running")
CheckIfGameRunning()