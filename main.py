import tkinter as tk
from tkinter import ttk, messagebox
import json
import hashlib
import os
import uuid
from datetime import datetime

DATA_DIR = "data"
DATA_USERS = os.path.join(DATA_DIR, "users.json")
DATA_ROOMS = os.path.join(DATA_DIR, "rooms.json")
DATA_RES   = os.path.join(DATA_DIR, "reservations.json")

# ─────────────────────────────────────────
#  UTILITIES
# ─────────────────────────────────────────

def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)
    for path in [DATA_USERS, DATA_ROOMS, DATA_RES]:
        if not os.path.exists(path):
            with open(path, "w") as f:
                json.dump([], f)

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

def load_json(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

def load_users():        return load_json(DATA_USERS)
def load_rooms():        return load_json(DATA_ROOMS)
def load_reservations(): return load_json(DATA_RES)
def save_users(x):        save_json(DATA_USERS, x)
def save_rooms(x):        save_json(DATA_ROOMS, x)
def save_reservations(x): save_json(DATA_RES, x)

# ─────────────────────────────────────────
#  BUSINESS LOGIC
# ─────────────────────────────────────────

def date_overlap(s1, e1, s2, e2):
    return s1 < e2 and s2 < e1

def room_is_available(room_number, new_start, new_end):
    for r in load_reservations():
        if r["room_number"] == room_number and r["status"] == "reserved":
            os_ = datetime.strptime(r["start"], "%Y-%m-%d")
            oe  = datetime.strptime(r["end"],   "%Y-%m-%d")
            if date_overlap(new_start, new_end, os_, oe):
                return False
    return True

# ─────────────────────────────────────────
#  APP — FENETRE UNIQUE
# ─────────────────────────────────────────

class HotelApp(tk.Tk):
    """
    Fenêtre principale unique.
    Toutes les vues sont des Frames empilées ; on les fait monter avec show_frame().
    """
    C = {
        "bg":       "#1A1A2E",
        "panel":    "#16213E",
        "card":     "#0F3460",
        "accent":   "#E94560",
        "accent2":  "#533483",
        "text":     "#EAEAEA",
        "dim":      "#8892A4",
        "success":  "#2ECC71",
        "entry":    "#0D2137",
        "border":   "#264573",
    }

    def __init__(self):
        super().__init__()
        self.title("🏨  Hôtel Manager")
        self.geometry("960x640")
        self.resizable(False, False)
        self.configure(bg=self.C["bg"])

        self.current_user = None
        self.current_role = None

        # Conteneur de toutes les frames
        container = tk.Frame(self, bg=self.C["bg"])
        container.pack(fill="both", expand=True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for Cls in (LoginFrame, RegisterFrame,
                    AdminDashFrame, ManageRoomsFrame, ViewReservationsFrame, CheckoutFrame,
                    ClientDashFrame, MakeReservationFrame, MyReservationsFrame):
            f = Cls(container, self)
            self.frames[Cls.__name__] = f
            f.grid(row=0, column=0, sticky="nsew")

        self.show_frame("LoginFrame")

    def show_frame(self, name):
        f = self.frames[name]
        if hasattr(f, "on_show"):
            f.on_show()
        f.tkraise()

    def logout(self):
        self.current_user = None
        self.current_role = None
        self.show_frame("LoginFrame")

# ─────────────────────────────────────────
#  WIDGETS RÉUTILISABLES
# ─────────────────────────────────────────

def mk_entry(parent, C, show=None):
    return tk.Entry(parent, show=show,
                    bg=C["entry"], fg=C["text"], insertbackground=C["text"],
                    relief="flat", font=("Courier", 11), bd=0,
                    highlightthickness=1,
                    highlightbackground=C["border"],
                    highlightcolor=C["accent"])

def mk_button(parent, C, text, cmd, accent=False):
    return tk.Button(parent, text=text, command=cmd,
                     bg=C["accent"] if accent else C["card"],
                     fg=C["text"], relief="flat",
                     font=("Courier", 11, "bold"), cursor="hand2",
                     activebackground=C["accent2"], activeforeground=C["text"],
                     padx=12, pady=7)

def mk_sidebar(parent, app, nav_items):
    C = app.C
    side = tk.Frame(parent, bg=C["panel"], width=210)
    side.pack(side="left", fill="y")
    side.pack_propagate(False)

    tk.Label(side, text="🏨", font=("Courier", 32),
             bg=C["panel"], fg=C["accent"]).pack(pady=(28, 4))
    tk.Label(side, text="HÔTEL MANAGER",
             font=("Courier", 10, "bold"), bg=C["panel"], fg=C["text"]).pack()
    tk.Frame(side, bg=C["border"], height=1).pack(fill="x", padx=18, pady=14)

    for label, frame_name in nav_items:
        tk.Button(side, text=f"  {label}", anchor="w",
                  bg=C["panel"], fg=C["text"], relief="flat",
                  font=("Courier", 11), cursor="hand2",
                  activebackground=C["card"], activeforeground=C["accent"],
                  command=lambda fn=frame_name: app.show_frame(fn)
                  ).pack(fill="x", padx=8, pady=3)

    tk.Frame(side, bg=C["border"], height=1).pack(fill="x", padx=18, pady=14)
    tk.Button(side, text="  ⎋  Déconnexion", anchor="w",
              bg=C["panel"], fg=C["accent"], relief="flat",
              font=("Courier", 11), cursor="hand2",
              command=app.logout).pack(fill="x", padx=8)

def mk_treeview(parent, cols, height=16):
    """Crée un Treeview stylisé avec scrollbar."""
    C = HotelApp.C
    style = ttk.Style()
    style.theme_use("default")
    style.configure("H.Treeview",
                    background=C["card"], fieldbackground=C["card"],
                    foreground=C["text"], rowheight=28, font=("Courier", 10))
    style.configure("H.Treeview.Heading",
                    background=C["panel"], foreground=C["accent"],
                    font=("Courier", 10, "bold"), relief="flat")
    style.map("H.Treeview", background=[("selected", C["accent2"])])

    wrap = tk.Frame(parent, bg=C["bg"])
    wrap.pack(fill="both", expand=True)

    tree = ttk.Treeview(wrap, columns=cols, show="headings",
                        height=height, style="H.Treeview")
    sb   = ttk.Scrollbar(wrap, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")
    return tree

# ─────────────────────────────────────────
#  VUE : CONNEXION
# ─────────────────────────────────────────

class LoginFrame(tk.Frame):
    def __init__(self, parent, app):
        C = app.C
        super().__init__(parent, bg=C["bg"])
        self.app = app

        # Panneau gauche décoratif
        left = tk.Frame(self, bg=C["panel"], width=400)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)
        tk.Label(left, text="🏨", font=("Courier", 64),
                 bg=C["panel"], fg=C["accent"]).place(relx=.5, rely=.36, anchor="center")
        tk.Label(left, text="HÔTEL MANAGER",
                 font=("Courier", 20, "bold"), bg=C["panel"], fg=C["text"]
                 ).place(relx=.5, rely=.52, anchor="center")
        tk.Label(left, text="Système de gestion hôtelière",
                 font=("Courier", 9), bg=C["panel"], fg=C["dim"]
                 ).place(relx=.5, rely=.60, anchor="center")

        # Formulaire
        right = tk.Frame(self, bg=C["bg"])
        right.pack(side="right", fill="both", expand=True)
        box = tk.Frame(right, bg=C["bg"])
        box.place(relx=.5, rely=.5, anchor="center")

        tk.Label(box, text="CONNEXION", font=("Courier", 20, "bold"),
                 bg=C["bg"], fg=C["text"]).grid(row=0, column=0, pady=(0, 24), sticky="w")

        tk.Label(box, text="Nom d'utilisateur", font=("Courier", 9),
                 bg=C["bg"], fg=C["dim"]).grid(row=1, column=0, sticky="w")
        self.user_e = mk_entry(box, C)
        self.user_e.grid(row=2, column=0, sticky="ew", ipady=8, pady=(3, 14))

        tk.Label(box, text="Mot de passe", font=("Courier", 9),
                 bg=C["bg"], fg=C["dim"]).grid(row=3, column=0, sticky="w")
        self.pass_e = mk_entry(box, C, show="*")
        self.pass_e.grid(row=4, column=0, sticky="ew", ipady=8, pady=(3, 20))

        mk_button(box, C, "  Se connecter  →", self.login, accent=True
                  ).grid(row=5, column=0, sticky="ew", pady=4)
        tk.Label(box, text="Pas encore de compte ?",
                 font=("Courier", 9), bg=C["bg"], fg=C["dim"]
                 ).grid(row=6, column=0, pady=(10, 2))
        mk_button(box, C, "  Créer un compte",
                  lambda: app.show_frame("RegisterFrame")
                  ).grid(row=7, column=0, sticky="ew")

        box.columnconfigure(0, minsize=280)
        self.user_e.bind("<Return>", lambda e: self.pass_e.focus())
        self.pass_e.bind("<Return>", lambda e: self.login())

    def login(self):
        u, p = self.user_e.get().strip(), self.pass_e.get()
        if not u or not p:
            messagebox.showerror("Erreur", "Remplissez tous les champs"); return
        for usr in load_users():
            if usr["username"] == u and usr["password"] == hash_password(p):
                self.app.current_user = u
                self.app.current_role = usr["role"]
                self.pass_e.delete(0, tk.END)
                self.user_e.delete(0, tk.END)
                self.app.show_frame("AdminDashFrame" if usr["role"] == "admin" else "ClientDashFrame")
                return
        messagebox.showerror("Erreur", "Identifiants incorrects")

# ─────────────────────────────────────────
#  VUE : INSCRIPTION
# ─────────────────────────────────────────

class RegisterFrame(tk.Frame):
    def __init__(self, parent, app):
        C = app.C
        super().__init__(parent, bg=C["bg"])
        self.app = app
        box = tk.Frame(self, bg=C["bg"])
        box.place(relx=.5, rely=.5, anchor="center")

        tk.Label(box, text="CRÉER UN COMPTE", font=("Courier", 20, "bold"),
                 bg=C["bg"], fg=C["text"]).grid(row=0, column=0, pady=(0, 24), sticky="w")

        fields = [("Nom d'utilisateur", "user_e", {}),
                  ("Mot de passe",      "pass_e", {"show": "*"}),
                  ("Confirmer",         "conf_e", {"show": "*"})]
        for i, (lbl, attr, kw) in enumerate(fields):
            tk.Label(box, text=lbl, font=("Courier", 9),
                     bg=C["bg"], fg=C["dim"]).grid(row=i*2+1, column=0, sticky="w")
            e = mk_entry(box, C, **kw)
            e.grid(row=i*2+2, column=0, sticky="ew", ipady=8, pady=(3, 14))
            setattr(self, attr, e)

        mk_button(box, C, "  Créer le compte  →", self.register, accent=True
                  ).grid(row=7, column=0, sticky="ew", pady=4)
        mk_button(box, C, "  ← Retour à la connexion",
                  lambda: app.show_frame("LoginFrame")
                  ).grid(row=8, column=0, sticky="ew")
        box.columnconfigure(0, minsize=280)

    def register(self):
        u, p, c = (self.user_e.get().strip(),
                   self.pass_e.get(), self.conf_e.get())
        if not u or not p:
            messagebox.showerror("Erreur", "Remplissez tous les champs"); return
        if len(p) < 4:
            messagebox.showerror("Erreur", "Mot de passe trop court (min 4)"); return
        if p != c:
            messagebox.showerror("Erreur", "Les mots de passe ne correspondent pas"); return
        users = load_users()
        if any(x["username"] == u for x in users):
            messagebox.showerror("Erreur", "Nom d'utilisateur déjà pris"); return
        users.append({"username": u, "password": hash_password(p), "role": "client"})
        save_users(users)
        messagebox.showinfo("Succès", f"Compte créé pour {u} !")
        for e in (self.user_e, self.pass_e, self.conf_e): e.delete(0, tk.END)
        self.app.show_frame("LoginFrame")

# ─────────────────────────────────────────
#  VUE : ADMIN — DASHBOARD
# ─────────────────────────────────────────

ADMIN_NAV = [("🛏  Gérer les chambres",  "ManageRoomsFrame"),
             ("📋  Réservations",        "ViewReservationsFrame"),
             ("✅  Check-out client",    "CheckoutFrame")]

CLIENT_NAV = [("🛏  Réserver",          "MakeReservationFrame"),
              ("📋  Mes réservations",   "MyReservationsFrame")]

class AdminDashFrame(tk.Frame):
    def __init__(self, parent, app):
        C = app.C
        super().__init__(parent, bg=C["bg"])
        self.app = app
        mk_sidebar(self, app, ADMIN_NAV)
        self.main = tk.Frame(self, bg=C["bg"])
        self.main.pack(side="right", fill="both", expand=True, padx=40, pady=36)

        tk.Label(self.main, text="Tableau de bord",
                 font=("Courier", 20, "bold"), bg=C["bg"], fg=C["text"]).pack(anchor="w")
        tk.Label(self.main, text="Vue d'ensemble de l'hôtel",
                 font=("Courier", 9), bg=C["bg"], fg=C["dim"]).pack(anchor="w", pady=(4, 24))
        self.stats = tk.Frame(self.main, bg=C["bg"])
        self.stats.pack(fill="x")

    def on_show(self):
        C = self.app.C
        for w in self.stats.winfo_children(): w.destroy()
        rooms  = load_rooms()
        res    = load_reservations()
        active = [r for r in res if r["status"] == "reserved"]
        ca     = sum(float(r["total"]) for r in res if r["status"] == "completed")
        for val, lbl, col in [
            (len(rooms),    "Chambres",          C["accent"]),
            (len(active),   "Réservations act.", C["success"]),
            (len(res),      "Total réservations",C["accent2"]),
            (f"{ca:.0f}€",  "CA réalisé",        "#F39C12"),
        ]:
            card = tk.Frame(self.stats, bg=C["card"], padx=22, pady=16)
            card.pack(side="left", padx=8)
            tk.Label(card, text=str(val), font=("Courier", 24, "bold"),
                     bg=C["card"], fg=col).pack()
            tk.Label(card, text=lbl, font=("Courier", 9),
                     bg=C["card"], fg=C["dim"]).pack()

# ─────────────────────────────────────────
#  VUE : ADMIN — GÉRER LES CHAMBRES
# ─────────────────────────────────────────

class ManageRoomsFrame(tk.Frame):
    def __init__(self, parent, app):
        C = app.C
        super().__init__(parent, bg=C["bg"])
        self.app = app
        mk_sidebar(self, app, ADMIN_NAV)

        main = tk.Frame(self, bg=C["bg"])
        main.pack(side="right", fill="both", expand=True, padx=30, pady=30)

        tk.Label(main, text="Gérer les chambres",
                 font=("Courier", 18, "bold"), bg=C["bg"], fg=C["text"]).pack(anchor="w", pady=(0, 16))

        # Formulaire ajout
        form = tk.Frame(main, bg=C["panel"], padx=20, pady=16)
        form.pack(fill="x", pady=(0, 18))
        row = tk.Frame(form, bg=C["panel"])
        row.pack(fill="x")

        for lbl, attr in [("Numéro", "num_e"), ("Type", "type_e"), ("Prix / nuit (€)", "price_e")]:
            col = tk.Frame(row, bg=C["panel"])
            col.pack(side="left", padx=10, expand=True, fill="x")
            tk.Label(col, text=lbl, font=("Courier", 9),
                     bg=C["panel"], fg=C["dim"]).pack(anchor="w")
            e = mk_entry(col, C)
            e.pack(fill="x", ipady=6, pady=2)
            setattr(self, attr, e)

        mk_button(form, C, "  + Ajouter", self.add_room, accent=True
                  ).pack(anchor="e", pady=(10, 0))

        # Liste
        self.lb = tk.Listbox(main, bg=C["card"], fg=C["text"],
                             font=("Courier", 11), relief="flat",
                             selectbackground=C["accent"], bd=0,
                             highlightthickness=0)
        self.lb.pack(fill="both", expand=True)

    def on_show(self):
        self.lb.delete(0, tk.END)
        for r in load_rooms():
            self.lb.insert(tk.END,
                f"  Chambre {r['number']:>4}  |  {r['type']:<15}  |  {float(r['price']):.2f} €/nuit")

    def add_room(self):
        n, t, p = self.num_e.get().strip(), self.type_e.get().strip(), self.price_e.get().strip()
        if not n or not t or not p:
            messagebox.showerror("Erreur", "Tous les champs sont obligatoires"); return
        try:
            price = float(p)
            if price <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Erreur", "Prix invalide"); return
        rooms = load_rooms()
        if any(r["number"] == n for r in rooms):
            messagebox.showerror("Erreur", f"Chambre {n} existe déjà"); return
        rooms.append({"number": n, "type": t, "price": price})
        save_rooms(rooms)
        for e in (self.num_e, self.type_e, self.price_e): e.delete(0, tk.END)
        self.on_show()
        messagebox.showinfo("Succès", f"Chambre {n} ajoutée ✓")

# ─────────────────────────────────────────
#  VUE : ADMIN — VOIR RÉSERVATIONS
# ─────────────────────────────────────────

class ViewReservationsFrame(tk.Frame):
    def __init__(self, parent, app):
        C = app.C
        super().__init__(parent, bg=C["bg"])
        self.app = app
        mk_sidebar(self, app, ADMIN_NAV)

        main = tk.Frame(self, bg=C["bg"])
        main.pack(side="right", fill="both", expand=True, padx=30, pady=30)
        tk.Label(main, text="Toutes les réservations",
                 font=("Courier", 18, "bold"), bg=C["bg"], fg=C["text"]).pack(anchor="w", pady=(0, 16))

        cols = ("Client", "Chambre", "Arrivée", "Départ", "Total", "Statut")
        self.tree = mk_treeview(main, cols)
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=118)
        self.tree.column("Client", width=150)

    def on_show(self):
        for row in self.tree.get_children(): self.tree.delete(row)
        for r in load_reservations():
            s = "✅ Réservé" if r["status"] == "reserved" else "☑️ Terminé"
            self.tree.insert("", tk.END, values=(
                r["client"], f"#{r['room_number']}", r["start"], r["end"],
                f"{float(r['total']):.2f}€", s))

# ─────────────────────────────────────────
#  VUE : ADMIN — CHECK-OUT
# ─────────────────────────────────────────

class CheckoutFrame(tk.Frame):
    def __init__(self, parent, app):
        C = app.C
        super().__init__(parent, bg=C["bg"])
        self.app = app
        self.active = []
        mk_sidebar(self, app, ADMIN_NAV)

        main = tk.Frame(self, bg=C["bg"])
        main.pack(side="right", fill="both", expand=True, padx=30, pady=30)
        tk.Label(main, text="Check-out clients",
                 font=("Courier", 18, "bold"), bg=C["bg"], fg=C["text"]).pack(anchor="w", pady=(0, 16))

        self.lb = tk.Listbox(main, bg=C["card"], fg=C["text"],
                             font=("Courier", 11), relief="flat",
                             selectbackground=C["accent"], bd=0,
                             highlightthickness=0, height=16)
        self.lb.pack(fill="both", expand=True, pady=(0, 14))
        mk_button(main, C, "  ✓  Confirmer le check-out", self.checkout, accent=True
                  ).pack(anchor="e")

    def on_show(self):
        self.lb.delete(0, tk.END)
        self.active = [r for r in load_reservations() if r["status"] == "reserved"]
        if not self.active:
            self.lb.insert(tk.END, "  Aucune réservation active.")
        for r in self.active:
            self.lb.insert(tk.END,
                f"  {r['client']}  |  Chambre {r['room_number']}  |  {r['start']} → {r['end']}")

    def checkout(self):
        if not self.lb.curselection():
            messagebox.showwarning("Attention", "Sélectionnez une réservation"); return
        sel = self.active[self.lb.curselection()[0]]
        res = load_reservations()
        for r in res:
            if r.get("id") == sel.get("id"):
                r["status"] = "completed"; break
        save_reservations(res)
        messagebox.showinfo("Succès", f"{sel['client']} checké-out ✓")
        self.on_show()

# ─────────────────────────────────────────
#  VUE : CLIENT — DASHBOARD
# ─────────────────────────────────────────

class ClientDashFrame(tk.Frame):
    def __init__(self, parent, app):
        C = app.C
        super().__init__(parent, bg=C["bg"])
        self.app = app
        mk_sidebar(self, app, CLIENT_NAV)

        self.main = tk.Frame(self, bg=C["bg"])
        self.main.pack(side="right", fill="both", expand=True, padx=40, pady=36)
        tk.Label(self.main, text="Espace Client",
                 font=("Courier", 20, "bold"), bg=C["bg"], fg=C["text"]).pack(anchor="w")
        self.welcome = tk.Label(self.main, text="", font=("Courier", 9),
                                bg=C["bg"], fg=C["dim"])
        self.welcome.pack(anchor="w", pady=(4, 24))
        self.stats = tk.Frame(self.main, bg=C["bg"])
        self.stats.pack(fill="x")

    def on_show(self):
        C = self.app.C
        self.welcome.config(text=f"Bienvenue, {self.app.current_user} 👋")
        for w in self.stats.winfo_children(): w.destroy()
        my  = [r for r in load_reservations() if r["client"] == self.app.current_user]
        act = [r for r in my if r["status"] == "reserved"]
        tot = sum(float(r["total"]) for r in my)
        for val, lbl, col in [
            (len(my),      "Mes réservations", C["accent"]),
            (len(act),     "En cours",          C["success"]),
            (f"{tot:.0f}€","Total dépensé",     "#F39C12"),
        ]:
            card = tk.Frame(self.stats, bg=C["card"], padx=22, pady=16)
            card.pack(side="left", padx=8)
            tk.Label(card, text=str(val), font=("Courier", 24, "bold"),
                     bg=C["card"], fg=col).pack()
            tk.Label(card, text=lbl, font=("Courier", 9),
                     bg=C["card"], fg=C["dim"]).pack()

# ─────────────────────────────────────────
#  VUE : CLIENT — FAIRE UNE RÉSERVATION
# ─────────────────────────────────────────

class MakeReservationFrame(tk.Frame):
    def __init__(self, parent, app):
        C = app.C
        super().__init__(parent, bg=C["bg"])
        self.app  = app
        self.rooms = []
        mk_sidebar(self, app, CLIENT_NAV)

        main = tk.Frame(self, bg=C["bg"])
        main.pack(side="right", fill="both", expand=True, padx=30, pady=30)
        tk.Label(main, text="Réserver une chambre",
                 font=("Courier", 18, "bold"), bg=C["bg"], fg=C["text"]).pack(anchor="w", pady=(0, 16))

        # Dates
        form = tk.Frame(main, bg=C["panel"], padx=20, pady=16)
        form.pack(fill="x", pady=(0, 16))
        row = tk.Frame(form, bg=C["panel"])
        row.pack(fill="x")
        for lbl, attr in [("Date d'arrivée  (YYYY-MM-DD)", "start_e"),
                           ("Date de départ  (YYYY-MM-DD)", "end_e")]:
            col = tk.Frame(row, bg=C["panel"])
            col.pack(side="left", padx=10, expand=True, fill="x")
            tk.Label(col, text=lbl, font=("Courier", 9),
                     bg=C["panel"], fg=C["dim"]).pack(anchor="w")
            e = mk_entry(col, C)
            e.pack(fill="x", ipady=6, pady=2)
            setattr(self, attr, e)

        # Liste chambres
        tk.Label(main, text="Chambres disponibles :", font=("Courier", 9),
                 bg=C["bg"], fg=C["dim"]).pack(anchor="w", pady=(0, 4))
        self.lb = tk.Listbox(main, bg=C["card"], fg=C["text"],
                             font=("Courier", 11), relief="flat",
                             selectbackground=C["accent"], bd=0,
                             highlightthickness=0, height=11)
        self.lb.pack(fill="both", expand=True, pady=(0, 12))

        bot = tk.Frame(main, bg=C["bg"])
        bot.pack(fill="x")
        self.price_lbl = tk.Label(bot, text="", font=("Courier", 11, "bold"),
                                  bg=C["bg"], fg=C["success"])
        self.price_lbl.pack(side="left")
        mk_button(bot, C, "  ✓  Confirmer", self.reserve, accent=True).pack(side="right")

        self.lb.bind("<<ListboxSelect>>", self.update_price)
        self.start_e.bind("<KeyRelease>", self.update_price)
        self.end_e.bind("<KeyRelease>",   self.update_price)

    def on_show(self):
        self.lb.delete(0, tk.END)
        self.rooms = load_rooms()
        for r in self.rooms:
            self.lb.insert(tk.END,
                f"  Chambre {r['number']:>4}  |  {r['type']:<15}  |  {float(r['price']):.2f} €/nuit")
        self.price_lbl.config(text="")

    def update_price(self, _=None):
        try:
            s = datetime.strptime(self.start_e.get().strip(), "%Y-%m-%d")
            e = datetime.strptime(self.end_e.get().strip(),   "%Y-%m-%d")
            if e <= s or not self.lb.curselection(): return
            room   = self.rooms[self.lb.curselection()[0]]
            nights = (e - s).days
            total  = nights * float(room["price"])
            self.price_lbl.config(
                text=f"{nights} nuit(s) × {float(room['price']):.2f}€ = {total:.2f}€")
        except: self.price_lbl.config(text="")

    def reserve(self):
        if not self.lb.curselection():
            messagebox.showwarning("Attention", "Sélectionnez une chambre"); return
        try:
            start = datetime.strptime(self.start_e.get().strip(), "%Y-%m-%d")
            end   = datetime.strptime(self.end_e.get().strip(),   "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Erreur", "Format date invalide (YYYY-MM-DD)"); return
        if end <= start:
            messagebox.showerror("Erreur", "La date de fin doit être après la date de début"); return
        room = self.rooms[self.lb.curselection()[0]]
        if not room_is_available(room["number"], start, end):
            messagebox.showerror("Erreur", "Chambre déjà réservée sur ces dates"); return
        nights = (end - start).days
        total  = nights * float(room["price"])
        reservations = load_reservations()
        reservations.append({
            "id":          str(uuid.uuid4()),
            "client":      self.app.current_user,
            "room_number": room["number"],
            "start":       self.start_e.get().strip(),
            "end":         self.end_e.get().strip(),
            "total":       total,
            "status":      "reserved"
        })
        save_reservations(reservations)
        messagebox.showinfo("Succès",
            f"Réservation confirmée !\n{nights} nuit(s) × {float(room['price']):.2f}€ = {total:.2f}€")
        self.start_e.delete(0, tk.END)
        self.end_e.delete(0, tk.END)
        self.price_lbl.config(text="")

# ─────────────────────────────────────────
#  VUE : CLIENT — MES RÉSERVATIONS
# ─────────────────────────────────────────

class MyReservationsFrame(tk.Frame):
    def __init__(self, parent, app):
        C = app.C
        super().__init__(parent, bg=C["bg"])
        self.app = app
        mk_sidebar(self, app, CLIENT_NAV)

        main = tk.Frame(self, bg=C["bg"])
        main.pack(side="right", fill="both", expand=True, padx=30, pady=30)
        tk.Label(main, text="Mes réservations",
                 font=("Courier", 18, "bold"), bg=C["bg"], fg=C["text"]).pack(anchor="w", pady=(0, 16))

        cols = ("Chambre", "Arrivée", "Départ", "Nuits", "Total", "Statut")
        self.tree = mk_treeview(main, cols)
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=120)

    def on_show(self):
        for row in self.tree.get_children(): self.tree.delete(row)
        for r in load_reservations():
            if r["client"] != self.app.current_user: continue
            try:
                nights = (datetime.strptime(r["end"],   "%Y-%m-%d") -
                          datetime.strptime(r["start"], "%Y-%m-%d")).days
            except: nights = "?"
            s = "✅ Réservé" if r["status"] == "reserved" else "☑️ Terminé"
            self.tree.insert("", tk.END, values=(
                f"#{r['room_number']}", r["start"], r["end"],
                nights, f"{float(r['total']):.2f}€", s))

# ─────────────────────────────────────────
#  LANCEMENT
# ─────────────────────────────────────────

ensure_data_dir()
app = HotelApp()
app.mainloop()