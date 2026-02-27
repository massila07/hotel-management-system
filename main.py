import tkinter as tk
from tkinter import messagebox
import json

def load_users():
    try:
        with open("data/users.json", "r") as file:
            return json.load(file)
    except:
        return []

def load_rooms():
    try:
        with open("data/rooms.json", "r") as file:
            return json.load(file)
    except:
        return []

def save_rooms(rooms):
    with open("data/rooms.json", "w") as file:
        json.dump(rooms, file, indent=4)

def open_admin_dashboard():
    dashboard = tk.Toplevel()
    dashboard.title("Admin Dashboard")
    dashboard.geometry("400x300")

    tk.Label(dashboard, text="Admin Panel", font=("Arial", 16)).pack(pady=20)

    tk.Button(dashboard, text="Manage Rooms", width=20, command=manage_rooms_window).pack(pady=5)
    tk.Button(dashboard, text="View Reservations", width=20).pack(pady=5)
    tk.Button(dashboard, text="Check-in Client", width=20).pack(pady=5)
    tk.Button(dashboard, text="Check-out Client", width=20).pack(pady=5)

def open_client_dashboard():
    dashboard = tk.Toplevel()
    dashboard.title("Client Dashboard")
    dashboard.geometry("400x300")

    tk.Label(dashboard, text="Client Panel", font=("Arial", 16)).pack(pady=20)

    tk.Button(dashboard, text="View Available Rooms", width=20).pack(pady=5)
    tk.Button(dashboard, text="Make Reservation", width=20, command=make_reservation_window).pack(pady=5)
    tk.Button(dashboard, text="My Reservations", width=20).pack(pady=5)

def manage_rooms_window():
    window = tk.Toplevel()
    window.title("Manage Rooms")
    window.geometry("400x400")

    tk.Label(window, text="Room Number").pack()
    number_entry = tk.Entry(window)
    number_entry.pack()

    tk.Label(window, text="Room Type").pack()
    type_entry = tk.Entry(window)
    type_entry.pack()

    tk.Label(window, text="Price per Night").pack()
    price_entry = tk.Entry(window)
    price_entry.pack()

    def add_room():
        number = number_entry.get()
        room_type = type_entry.get()
        price = price_entry.get()

        rooms = load_rooms()

        new_room = {
            "number": number,
            "type": room_type,
            "price": price,
            "status": "available"
        }

        rooms.append(new_room)
        save_rooms(rooms)

        messagebox.showinfo("Success", "Room added")

    tk.Button(window, text="Add Room", command=add_room).pack(pady=10)

    rooms_list = tk.Listbox(window, width=50)
    rooms_list.pack(pady=10)

    def refresh_rooms():
        rooms_list.delete(0, tk.END)
        rooms = load_rooms()
        for room in rooms:
            rooms_list.insert(tk.END, f"Room {room['number']} | {room['type']} | {room['price']} | {room['status']}")

    tk.Button(window, text="Refresh List", command=refresh_rooms).pack()

def load_reservations():
    try:
        with open("data/reservations.json", "r") as file:
            return json.load(file)
    except:
        return []

def save_reservations(reservations):
    with open("data/reservations.json", "w") as file:
        json.dump(reservations, file, indent=4)

def make_reservation_window():
    window = tk.Toplevel()
    window.title("Make Reservation")
    window.geometry("400x400")

    tk.Label(window, text="Available Rooms", font=("Arial", 14)).pack(pady=10)

    rooms_list = tk.Listbox(window, width=50)
    rooms_list.pack(pady=10)

    rooms = load_rooms()

    available_rooms = []
    for room in rooms:
        if room["status"] == "available":
            available_rooms.append(room)
            rooms_list.insert(tk.END, f"Room {room['number']} | {room['type']} | {room['price']}")

    tk.Label(window, text="Client Name").pack()
    name_entry = tk.Entry(window)
    name_entry.pack()

    def reserve_room():
        selection = rooms_list.curselection()
        if not selection:
            messagebox.showerror("Error", "Select a room")
            return

        selected_room = available_rooms[selection[0]]
        client_name = name_entry.get()

        reservations = load_reservations()

        new_reservation = {
            "client": client_name,
            "room_number": selected_room["number"],
            "status": "reserved"
        }

        reservations.append(new_reservation)
        save_reservations(reservations)

        rooms = load_rooms()
        for room in rooms:
            if room["number"] == selected_room["number"]:
                room["status"] = "occupied"
        save_rooms(rooms)

        messagebox.showinfo("Success", "Reservation created")

    tk.Button(window, text="Reserve", command=reserve_room).pack(pady=10)

def login():
    username = username_entry.get()
    password = password_entry.get()

    users = load_users()

    for user in users:
        if user["username"] == username and user["password"] == password:
            messagebox.showinfo("Success", f"Welcome {user['role']}")
            root.withdraw()

            if user["role"] == "admin":
                open_admin_dashboard()
            else:
                open_client_dashboard()
            return

    messagebox.showerror("Error", "Invalid credentials")

def register():
    username = username_entry.get()
    password = password_entry.get()

    users = load_users()

    new_user = {
        "username": username,
        "password": password,
        "role": "client"
    }

    users.append(new_user)

    with open("data/users.json", "w") as file:
        json.dump(users, file, indent=4)

    messagebox.showinfo("Success", "Client registered")

root = tk.Tk()
root.title("Hotel Management System")
root.geometry("400x300")

title = tk.Label(root, text="Hotel Management System", font=("Arial", 16))
title.pack(pady=20)

tk.Label(root, text="Username / Email").pack()
username_entry = tk.Entry(root, width=30)
username_entry.pack(pady=5)

tk.Label(root, text="Password").pack()
password_entry = tk.Entry(root, show="*", width=30)
password_entry.pack(pady=5)

tk.Button(root, text="Login", width=20, command=login).pack(pady=10)
tk.Button(root, text="Register as Client", width=20, command=register).pack()

root.mainloop()