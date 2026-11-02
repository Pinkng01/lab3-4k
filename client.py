import requests
from requests.auth import HTTPBasicAuth

BASE_URL = "http://127.0.0.1:8000"
AUTH = HTTPBasicAuth("admin", "secret123")

def get_all_items():
    print("\n=== CATALOGUE ===")
    try:
        response = requests.get(f"{BASE_URL}/items", auth=AUTH)
        if response.status_code == 200:
            items = response.json()
            if not items:
                print("Catalogue is empty.")
            else:
                for item in items:
                    print(f"ID: {item['id']} | {item['name']} | ${item['price']} | {item['size']} | {item['weight']}kg | {item['color']}")
        elif response.status_code == 401:
            print("Error: 401 Unauthorized. Check your credentials or delete user_cat.db and restart server.")
        else:
            print(f"Error: {response.status_code}")
    except Exception as e:
        print(f"Connection error: {e}")

def add_item_ui(name=None, price=None, size=None, weight=None, color=None):
    # Если параметры не переданы, запрашиваем ввод
    if name is None:
        print("\n--- Adding New Item ---")
        try:
            name = input("Name: ")
            price = float(input("Price: "))
            size = input("Size: ")
            weight = float(input("Weight: "))
            color = input("Color: ")
        except ValueError:
            print("Invalid input! Price and Weight must be numbers.")
            return

    payload = {"name": name, "price": price, "size": size, "weight": weight, "color": color}
    response = requests.post(f"{BASE_URL}/items", json=payload, auth=AUTH)
    if response.status_code == 201:
        print(f"Successfully added: {name}")
    else:
        print(f"Failed to add item {name}. Status: {response.status_code}")

def populate_db():
    print("\n--- Populating Database ---")
    test_items = [
        ("Gaming Laptop", 1500.0, "Medium", 2.3, "Grey"),
        ("Mechanical Keyboard", 120.0, "Small", 0.8, "Black"),
        ("UltraWide Monitor", 450.0, "Large", 7.5, "Silver"),
        ("Wireless Mouse", 80.0, "Tiny", 0.1, "White"),
        ("Gaming Chair", 250.0, "Huge", 20.0, "Red/Black"),
        ("USB-C Hub", 45.0, "Pocket", 0.1, "Space Grey"),
        ("Webcam 4K", 110.0, "Small", 0.3, "Black"),
        ("Studio Mic", 200.0, "Medium", 1.2, "Gold")
    ]
    for item in test_items:
        add_item_ui(*item)
    print("\nDone! Database populated.")

def update_item_ui():
    print("\n--- Updating Item ---")
    try:
        item_id = int(input("Enter Item ID to update: "))
        name = input("New Name: ")
        price = float(input("New Price: "))
        size = input("New Size: ")
        weight = float(input("New Weight: "))
        color = input("New Color: ")
        
        payload = {"name": name, "price": price, "size": size, "weight": weight, "color": color}
        response = requests.put(f"{BASE_URL}/items/{item_id}", json=payload, auth=AUTH)
        if response.status_code == 200:
            print("Successfully updated!")
        else:
            print(f"Failed. Item with ID {item_id} might not exist.")
    except ValueError:
        print("Invalid input!")

def delete_item_ui():
    print("\n--- Deleting Item ---")
    try:
        item_id = int(input("Enter Item ID to delete: "))
        response = requests.delete(f"{BASE_URL}/items/{item_id}", auth=AUTH)
        if response.status_code == 200:
            print(response.json().get("message", "Deleted."))
        else:
            print("Failed to delete. Check ID.")
    except ValueError:
        print("Invalid ID!")

def main_menu():
    while True:
        print("\n" + "="*35)
        print("   STORE MANAGEMENT SYSTEM   ")
        print("="*35)
        print("1. View all items")
        print("2. Add new item (Manual)")
        print("3. Update item")
        print("4. Delete item")
        print("5. POPULATE DATABASE (Auto-add)")
        print("0. Exit")
        
        choice = input("\nSelect option: ")
        
        if choice == "1": get_all_items()
        elif choice == "2": add_item_ui()
        elif choice == "3": update_item_ui()
        elif choice == "4": delete_item_ui()
        elif choice == "5": populate_db()
        elif choice == "0":
            print("Goodbye!"); break
        else:
            print("Unknown option.")

if __name__ == "__main__":
    main_menu()