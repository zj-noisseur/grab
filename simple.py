base = 1

weather_multipliers = {
    1: 1.0,
    2: 1.1,
    3: 1.5,
}

traffic_multipliers = {
    1: 1.6,
    2: 1.2,
}

def distance(x, y):
    

def fare(weather, traffic):
    print(f"The trip is RM {base * weather_multipliers[weather] * traffic_multipliers[traffic]}")

while True:
    try:
        weather = int(input("1. Sunny \n2. Cloudy \n3. Storm \n"))
        if not (1 <= weather <= 3):
            print("Please insert a valid range only.")
            continue
        

        traffic = int(input("1. Peak hour \n2. Normal \n"))
        if not (1 <= traffic <= 2):
            print("Please choose either 1 or 2 only.")
            continue 
        fare(weather, traffic)
        choice = int(input("Do you still wish to continue? \n1. Yes \n2. No \n"))

        if choice == 1:
            break
        elif choice == 2:
            continue
        else:
            print("Please enter either 1 or 2 only.")

    except ValueError:
        print("Please provide only valid integers only.")
        continue



    
        

