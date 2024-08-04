import os
import shodan
import json
import re
import colorama
from colorama import Fore, Style

# colorama başlatma
colorama.init(autoreset=True)

# Get the current working directory
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# File names for storing API keys and dorks
API_KEY_FILE = os.path.join(CURRENT_DIR, "shodan_api_key.txt")
DORKS_FILE = os.path.join(CURRENT_DIR, "dorks.json")

def ensure_file_exists(file_path):
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            if file_path == DORKS_FILE:
                json.dump([], f)  # Create an empty list for dorks file
            print(f"{file_path} created successfully.")

def load_api_key():
    ensure_file_exists(API_KEY_FILE)
    if os.path.exists(API_KEY_FILE):
        with open(API_KEY_FILE, 'r') as f:
            api_key = f.read().strip()
            if api_key:
                message = f"Loaded API key from {API_KEY_FILE}"
                print_colored_box(message, Fore.YELLOW)
                return api_key
            else:
                print_colored_box("API key file is empty.", Fore.RED)
    else:
        print_colored_box(f"{API_KEY_FILE} does not exist.", Fore.RED)
    return None

def save_api_key(api_key):
    try:
        with open(API_KEY_FILE, 'w') as f:
            f.write(api_key)
        print_colored_box("API key saved successfully.", Fore.GREEN)
    except Exception as e:
        print_colored_box(f"Error saving API key: {e}", Fore.RED)

def load_dorks():
    ensure_file_exists(DORKS_FILE)
    if os.path.exists(DORKS_FILE):
        with open(DORKS_FILE, 'r') as f:
            try:
                dorks = json.load(f)
                message = f"Loaded dorks from {DORKS_FILE}"
                print_colored_box(message, Fore.GREEN)
                return dorks
            except json.JSONDecodeError:
                print_colored_box("Error decoding JSON. Returning empty list.", Fore.RED)
                return []
    else:
        print_colored_box(f"{DORKS_FILE} does not exist.", Fore.RED)
    return []

def save_dorks(dorks):
    try:
        with open(DORKS_FILE, 'w') as f:
            json.dump(dorks, f, indent=4)
        print_colored_box("Dorks saved successfully.", Fore.GREEN)
    except Exception as e:
        print_colored_box(f"Error saving dorks: {e}", Fore.RED)

def add_dork(dorks):
    while True:
        name = input(Fore.CYAN + Style.BRIGHT + "Enter dork name (leave blank to exit): " + Style.RESET_ALL)
        if not name:
            break
        dork = input(Fore.CYAN + Style.BRIGHT + "Enter dork (leave blank to exit): " + Style.RESET_ALL)
        if not dork:
            break
        dorks.append({"name": name, "dork": dork})
        message = f"Added dork: {name} - {dork}"
        print_colored_box(message, Fore.GREEN)
    save_dorks(dorks)

def delete_dork(dorks):
    if not dorks:
        print_colored_box("No dorks to delete.", Fore.RED)
        return
    max_len_name = max(len(dork['name']) for dork in dorks)
    max_len_dork = max(len(dork['dork']) for dork in dorks)
    col_width = max_len_name + max_len_dork + 5  # 5 for padding and separators

    for idx, dork in enumerate(dorks, 1):
        if idx % 4 == 1 and idx != 1:
            print()  # new line every 4 dorks
        print(Fore.YELLOW + f"{idx}. {dork['name']} - {dork['dork']}".ljust(col_width) + Style.RESET_ALL, end="")

    print()  # ensure there's a newline at the end

    while True:
        choice = input(Fore.CYAN + Style.BRIGHT + "\nEnter the number of the dork to delete (leave blank to exit): " + Style.RESET_ALL)
        if not choice:
            break
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(dorks):
                message = f"Deleting dork: {dorks[idx]['name']}"
                print_colored_box(message, Fore.GREEN)
                del dorks[idx]
                save_dorks(dorks)
                return
            else:
                print_colored_box("Invalid choice.", Fore.RED)
        except ValueError:
            print_colored_box("Invalid input. Please enter a number.", Fore.RED)

def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def search_shodan(api, dorks):
    if not dorks:
        print_colored_box("No dorks available. Please add dorks first.", Fore.RED)
        return
    max_len_name = max(len(dork['name']) for dork in dorks)
    max_len_dork = max(len(dork['dork']) for dork in dorks)
    col_width = max_len_name + max_len_dork + 5  # 5 for padding and separators

    for idx, dork in enumerate(dorks, 1):
        if idx % 4 == 1 and idx != 1:
            print()  # new line every 4 dorks
        print(Fore.YELLOW + f"{idx}. {dork['name']} - {dork['dork']}".ljust(col_width) + Style.RESET_ALL, end="")

    print()  # ensure there's a newline at the end

    while True:
        choice = input(Fore.CYAN + Style.BRIGHT + "\nSelect a dork to run (0 to return to menu): " + Style.RESET_ALL)
        if choice == "0":
            return
        try:
            choice = int(choice) - 1
            if 0 <= choice < len(dorks):
                selected_dork = dorks[choice]
                dork = selected_dork["dork"]
                country_code = input(Fore.CYAN + Style.BRIGHT + "Enter country code (e.g., US, leave blank for all): " + Style.RESET_ALL).upper()
                query = dork
                if country_code:
                    query += f" country:{country_code}"
                try:
                    results = api.search(query)
                    message = f"Total results: {results['total']}"
                    print_colored_box(message, Fore.GREEN)
                    if results['total'] > 0:
                        save_results(results['matches'], dork, country_code)
                    else:
                        print_colored_box("No results found.", Fore.RED)
                except shodan.APIError as e:
                    print_colored_box(f"Error: {e}", Fore.RED)
                return
            else:
                print_colored_box("Invalid choice. Please try again.", Fore.RED)
        except ValueError:
            print_colored_box("Invalid input. Please enter a number.", Fore.RED)

def save_results(results, dork, country_code):
    filename = sanitize_filename(dork)
    if country_code:
        filename += f"_{country_code}"
    filename += ".txt"
    filename = os.path.join(CURRENT_DIR, filename)
    try:
        with open(filename, 'w') as f:
            for result in results:
                ip = result['ip_str']
                f.write(f"{ip}\n")
        message = f"Results saved to {filename}."
        print_colored_box(message, Fore.GREEN)
    except Exception as e:
        print_colored_box(f"Error saving results: {e}", Fore.RED)

def print_colored_box(message, color):
    length = len(message) + 4
    print(color + Style.BRIGHT + "+" + "-" * length + "+")
    print("| " + message + " |")
    print("+" + "-" * length + "+" + Style.RESET_ALL)

def main():
    # Tool name
    banner = """\033[1m\033[96m
         __              ____ __            ______       __  
   _____/ /_  ____  ____/ / // / ____  ____/ / __ \_____/ /__
  / ___/ __ \/ __ \/ __  / // /_/ __ \/ __  / / / / ___/ //_/
 (__  ) / / / /_/ / /_/ /__  __/ / / / /_/ / /_/ / /  / ,<   
/____/_/ /_/\____/\__,_/  /_/ /_/ /_/\__,_/\____/_/  /_/|_|  

                       \t\t\t\033[96mby emachintag\033[0m
    \033[0m"""
    print(banner)

    api_key = load_api_key()
    if not api_key:
        api_key = input(Fore.CYAN + Style.BRIGHT + "Enter your Shodan API key: " + Style.RESET_ALL)
        save_api_key(api_key)

    api = shodan.Shodan(api_key)
    dorks = load_dorks()

    while True:
        print(Fore.GREEN + Style.BRIGHT + "1. Add dork" + Style.RESET_ALL)
        print(Fore.GREEN + Style.BRIGHT + "2. Search Shodan" + Style.RESET_ALL)
        print(Fore.GREEN + Style.BRIGHT + "3. Delete a dork" + Style.RESET_ALL)
        print(Fore.GREEN + Style.BRIGHT + "4. Enter API key" + Style.RESET_ALL)
        print(Fore.RED + Style.BRIGHT + "0. Exit" + Style.RESET_ALL)

        choice = input(Fore.CYAN + Style.BRIGHT + "Your choice: " + Style.RESET_ALL)

        if choice == "1":
            add_dork(dorks)
        elif choice == "2":
            search_shodan(api, dorks)
        elif choice == "3":
            delete_dork(dorks)
        elif choice == "4":
            api_key = input(Fore.CYAN + Style.BRIGHT + "Enter your new Shodan API key: " + Style.RESET_ALL)
            save_api_key(api_key)
            api = shodan.Shodan(api_key)
        elif choice == "0":
            break
        else:
            print_colored_box("Invalid choice, please try again.", Fore.RED)

if __name__ == "__main__":
    main()
