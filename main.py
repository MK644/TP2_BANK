from tkinter import *


import sqlite3

import random

from datetime import datetime, date

try:
    import winsound
except ImportError:          # Mac / Linux
    winsound = None


def jouer_son():
    if winsound:
        winsound.Beep(1000, 120)
        winsound.Beep(1400, 180)
    else:
        fenetre.bell()
################ connexion base de donner #########

connexion = sqlite3.connect("banque.db")
cursor = connexion.cursor()


############## CREER SI PAS EXISTANT / SOLDE BASE DE DONNER #########################33
#pour transfert
cursor.execute("CREATE TABLE IF NOT EXISTS history (SENDER INTEGER, RECEIVER INTEGER, AMOUNT INTEGER, DATE)")

#table pour account
cursor.execute("CREATE TABLE IF NOT EXISTS comptes (num_compte INTEGER, argent INTEGER, password TEXT, phrase_mot TEXT)")
#table pour numeros account possible
cursor.execute("CREATE TABLE IF NOT EXISTS numeros_restants (numero INTEGER)")
########################### NUMERO DE COMPTE #################################
# Première fois seulement : remplir la liste des numéros
cursor.execute("SELECT COUNT(*) FROM numeros_restants")
nb_restants = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM comptes")
nb_comptes = cursor.fetchone()[0]
if nb_restants == 0 and nb_comptes == 0:
    for n in range(101, 111):
        cursor.execute("INSERT INTO numeros_restants VALUES (?)", (n,))
    connexion.commit()

# Ta liste vient maintenant de la base

cursor.execute("SELECT numero FROM numeros_restants")
compte_num = [ligne[0] for ligne in cursor.fetchall()]



########### CONSOLE ################

def console_debut():
    print("Bonjour :")
    print(" - Tapez A, pour vous connecter à l’Application.")
    print(" - Tapez U, pour un nouvel Utilisateur.")

    choix = ""
    while choix != "A" and choix != "U":
        choix = input()
        choix = choix.upper()
        if choix == "U":
            if len(compte_num) == 0:
                print("Plus aucun numéro de compte disponible.")
                break

            num_compte = random.choice(compte_num)
            compte_num.remove(num_compte)
            argent = random.randint(100, 500)
            print(f"Bienvenue, voici votre numéro de compte {num_compte} ")

            password = input("Choisissez votre mot de passe et pressez sur ENTRÉE : ")
            password_conf = input("Confirmez votre mot de passe puis pressez sur ENTRÉE : ")
            while password_conf != password:
                password_conf = input("Les mots de passe ne correspondent pas, réessayez : ")
            print("Indiquez une phrase pour vous rappeler du mot de passe et pressez sur ENTRÉE.")
            phrase_mot = input()



            # Base de données METTRE LES INFOS RECOLTER
            cursor.execute("DELETE FROM numeros_restants WHERE numero = ?", (num_compte,))
            cursor.execute("INSERT INTO comptes VALUES (?, ?, ?, ?)", (num_compte, argent, password, phrase_mot))
            connexion.commit()

        ### SI A ECRAN APPARAIT




    connexion.close()

#########MDP ADMIN ###############################################

password_adm = "123"
nom_adm = "adm"


############################ FONCTION RECOLTE BASE DE DONNER ET MODIFIER ####################



    ## FONCTION RECOLTE MOTS DE PASSE CELON LE NOM DE L'utilisateur

                ## verification #####
def verification_mdp_client(numero_compte, mots_depasses):
    conn = sqlite3.connect("banque.db")
    curs = conn.cursor()

    curs.execute("SELECT password FROM comptes WHERE num_compte = ?", (int(numero_compte),))
    resultat = curs.fetchone()   # (mot_de_passe,) ou None si le compte n'existe pas
    conn.close()

    if resultat is None:
        return False             # compte inexistant
    return resultat[0] == mots_depasses

           ############## Recolte numeros ###########
def verification_mdp_admin(numero_compte, mots_depasses):


    return numero_compte == nom_adm and password_adm == mots_depasses

def Motsdepasses_oublié():
    numero = Numero_compte

    if Admin.get() == "admin":
        if numero == str(nom_adm):
            print(password_adm)
        else:
            print("Vous n'avez pas de compte admin")

    else:                                          # client
        if not numero.isdigit() or numero == str(nom_adm):
            print("Vous n'avez pas de compte client")
            return

        conn = sqlite3.connect("banque.db")
        curs = conn.cursor()
        curs.execute("SELECT password FROM comptes WHERE num_compte = ?", (int(numero),))
        resultat = curs.fetchone()                 # (mot_de_passe,) ou None
        conn.close()

        if resultat is None:
            print("Vous n'avez pas de compte client")
        else:
            print(resultat[0])

def info_compte(numero_compte):
    numero_compte = int(numero_compte)
    conn = sqlite3.connect("banque.db")
    curs = conn.cursor()
    curs.execute("SELECT argent FROM comptes WHERE num_compte = ?", (numero_compte,))
    solde = curs.fetchone()          # (argent,) ou None si le compte n'existe pas
    curs.execute("SELECT SENDER, RECEIVER, AMOUNT, DATE FROM history "
                 "WHERE SENDER = ? OR RECEIVER = ? ORDER BY rowid",
                 (numero_compte, numero_compte))
    historique = curs.fetchall()     # liste de (SENDER, RECEIVER, AMOUNT, DATE)
    conn.close()
    return (solde, historique)
def transfert(receiver, sender, amount):
    if not (str(receiver).isdigit() and str(amount).isdigit()):
        return "Numéro ou montant invalide"
    receiver, sender, amount = int(receiver), int(sender), int(amount)

    if receiver == sender:
        return "Vous ne pouvez pas vous envoyer de l'argent"
    if amount <= 0:
        return "Le montant doit être positif"
    if info_compte(receiver)[0] is None:
        return "Compte destinataire inexistant"
    if info_compte(sender)[0][0] < amount:
        return "Solde insuffisant"

    conn = sqlite3.connect("banque.db")
    curs = conn.cursor()
    date_actuelle = datetime.now().isoformat(sep=" ", timespec="seconds")
    curs.execute("INSERT INTO history(SENDER,RECEIVER,AMOUNT,DATE) VALUES(?,?,?,?)",
                 (sender, receiver, amount, date_actuelle))
    curs.execute("UPDATE comptes SET argent = argent + ? WHERE num_compte = ?", (amount, receiver))
    curs.execute("UPDATE comptes SET argent = argent - ? WHERE num_compte = ?", (amount, sender))
    conn.commit()
    conn.close()
    return "Virement effectué"
def modifier_balance(numero_compte, nouvelle_balance):
    conn = sqlite3.connect("banque.db")
    curs = conn.cursor()
    curs.execute("UPDATE comptes SET argent = ? WHERE num_compte = ?",
                 (int(nouvelle_balance), int(numero_compte)))
    conn.commit()
    ok = curs.rowcount > 0
    conn.close()
    return ok


def modifier_mots_passe(numero_compte, nouveau_mdp):
    conn = sqlite3.connect("banque.db")
    curs = conn.cursor()
    curs.execute("UPDATE comptes SET password = ? WHERE num_compte = ?",
                 (nouveau_mdp, int(numero_compte)))
    conn.commit()
    ok = curs.rowcount > 0
    conn.close()
    return ok


def recuperer_TOUTacoount():
    """Retourne une liste de tuples : [(num_compte, argent, password), ...]"""
    conn = sqlite3.connect("banque.db")
    curs = conn.cursor()
    curs.execute("SELECT num_compte, argent, password FROM comptes ORDER BY num_compte")
    resultat = curs.fetchall()
    conn.close()
    return resultat


def supprimer_compte(numero_compte):
    numero_compte = int(numero_compte)
    conn = sqlite3.connect("banque.db")
    curs = conn.cursor()
    curs.execute("DELETE FROM comptes WHERE num_compte = ?", (numero_compte,))
    ok = curs.rowcount > 0
    if ok:
        # le numéro redevient disponible, et son historique est effacé
        # pour qu'un futur compte avec ce numéro ne l'hérite pas
        curs.execute("DELETE FROM history WHERE SENDER = ? OR RECEIVER = ?",
                     (numero_compte, numero_compte))
        curs.execute("INSERT INTO numeros_restants VALUES (?)", (numero_compte,))
        if numero_compte not in compte_num:
            compte_num.append(numero_compte)
    conn.commit()
    conn.close()
    return ok
################################################### graphique ##########################################



def chart(parent, compte, actuel, width=500, height=300):
    compte = int(compte)
    historique = info_compte(compte)[1]      # (SENDER, RECEIVER, AMOUNT, DATE)

    # On remonte le temps à partir du solde actuel
    points = [{"date": datetime.now(), "y": actuel}]
    solde = actuel
    for sender, receiver, amount, d in reversed(historique):
        points.append({"date": d, "y": solde})          # solde après ce virement
        solde += amount if sender == compte else -amount  # solde avant ce virement
    if historique:
        points.append({"date": historique[0][3], "y": solde})  # solde de départ
    points.reverse()                                     # ordre chronologique

    canvas = Canvas(
        parent,
        width=width,
        height=height,
        bg="white",
        highlightthickness=0)

    margin_left = 65
    margin_right = 20
    margin_top = 25
    margin_bottom = 45

    graph_width = width - margin_left - margin_right
    graph_height = height - margin_top - margin_bottom

    def to_date(d):
        if isinstance(d, str):
            return datetime.fromisoformat(d)
        if isinstance(d, date) and not isinstance(d, datetime):
            return datetime.combine(d, datetime.min.time())
        return d

    points = sorted(points, key=lambda p: to_date(p["date"]))

    if not points:
        return canvas

    dates = [to_date(p["date"]) for p in points]
    values = [p["y"] for p in points]

    start = dates[0]
    end = dates[-1]
    middle = start + (end - start) / 2

    # Calcul automatique du minimum et maximum
    plus_bas = min(values)
    plus_haut = max(values)

    if plus_bas == plus_haut:
        plus_bas -= 1
        plus_haut += 1

    def px(d):
        if start == end:
            return margin_left + graph_width / 2
        return margin_left + (
                (d - start).total_seconds() /
                (end - start).total_seconds()
        ) * graph_width

    def py(y):
        return margin_top + (
                (plus_haut - y) / (plus_haut - plus_bas)
        ) * graph_height

    # Axe Y
    canvas.create_line(
        margin_left, margin_top,
        margin_left, height - margin_bottom,
        fill="black"
    )

    # Axe X
    canvas.create_line(
        margin_left, height - margin_bottom,
                     width - margin_right, height - margin_bottom,
        fill="black"
    )

    # Valeurs minimum et maximum
    canvas.create_text(
        margin_left - 10, py(plus_bas),
        text=str(plus_bas),
        anchor="e"
    )

    canvas.create_text(
        margin_left - 10, py(plus_haut),
        text=str(plus_haut),
        anchor="e"
    )

    # Valeur actuelle
    if actuel != plus_bas and actuel != plus_haut:
        canvas.create_text(
            margin_left - 10, py(actuel),
            text=str(actuel),
            anchor="e",
            fill="blue",
            font=("Arial", 9, "bold")
        )

        canvas.create_line(
            margin_left, py(actuel),
            width - margin_right, py(actuel),
            fill="blue",
            dash=(4, 3)
        )

    # Dates : début, milieu et fin
    for d in [start, middle, end]:
        x = px(d)

        canvas.create_line(
            x, height - margin_bottom,
            x, height - margin_bottom + 5,
            fill="black"
        )

        canvas.create_text(
            x, height - margin_bottom + 17,
            text=d.strftime("%d/%m/%y %H:%M"),
            font=("Arial", 8)
        )

    # Courbe uniquement
    coords = []

    for p in points:
        d = to_date(p["date"])
        coords.extend([px(d), py(p["y"])])

    if len(coords) >= 4:
        canvas.create_line(
            coords,
            fill="#2196F3",
            width=2,
            smooth=True
        )

    return canvas


############################# ACCUEIL ############################
def erreur_connexion():
    top = Toplevel(fenetre)                   # lié à la fenêtre principale
    top.title("Erreur")
    top.geometry("300x100")
    top.resizable(0, 0)

    #le bouton est empaqueté en premier pour rester tout en bas
    Button(top, text="OK", width=8, command=top.destroy).pack(side=BOTTOM, pady=5)

    Label(top, text="Renseignements d'ouverture de session erronés",
          font=("Arial", 9, "bold"), wraplength=280).pack(pady=(8, 2))
    Label(top, text="Veuillez vérifier vos données de connexion et réessayer",
          wraplength=280).pack()


def accueil():
    global fenetre,Numero_compte, Admin, champ2
    fenetre = Tk()
    fenetre.title("Accueil")
    fenetre.geometry("400x600")
    Label(fenetre, text="Banque Grasséenne").pack(pady=20)
    Label(fenetre, text="Type de connexion").pack()
    Admin = StringVar()  # variable Tkinter, pas un booléen
    Admin.set("client")
    def désactiver():
        if Admin.get() == "admin":
            Bouton2.config(state="disabled")  # bouton grisé, non cliquable
        else:
            Bouton2.config(state="normal")

    Radiobutton(fenetre, text="Admin", variable=Admin, value="admin", command=désactiver).pack(anchor=CENTER)
    Radiobutton(fenetre, text="Client", variable=Admin, value="client", command=désactiver).pack(anchor=CENTER)

    Label(fenetre, text="Numéro de compte").pack(pady=10)
    champ = Entry(fenetre)
    champ.pack(pady=10)
    champ2=None
    Numero_compte = champ.get()
    def motdepass(event):
        global champ2
        Label(fenetre, text="Mots de passes").place(relx=0.5, rely=0.4, anchor=CENTER)
        champ2=Entry(fenetre)
        champ2.place(relx=0.5, rely=0.45, anchor=CENTER)
    champ.bind("<Return>",motdepass)
    def désactiver():
        if Admin.get() == "admin":
            Bouton2.state=("Disable")

    def connexion():
        global Numero_compte
        if champ2 == None:
            motdepass(None)
        elif Admin.get() == "admin":
            if verification_mdp_admin(champ.get(), champ2.get()):
                session_Admin()
            else:
                erreur_connexion()
        elif Admin.get() == "client":
            if verification_mdp_client(champ.get(), champ2.get()):
                Numero_compte = champ.get()  # <-- ajouté
                session_client()
            else:
                erreur_connexion()
    Bouton1 = Button(fenetre, text="Ouvrir la session", command=connexion)
    Bouton1.place(relx=0.5, rely=0.6, anchor=CENTER)
    Bouton2 = Button(fenetre, text="Mots de passes oublié ?", command=Motsdepasses_oublié)
    Bouton2.place(relx=0.5, rely=0.67, anchor=CENTER)
    fenetre.mainloop()

#######################################ADMIN#######################################################3

def session_Admin():
    fenetre2 = Tk()
    liste=recuperer_TOUTacoount()
    fenetre2.title("Admin")
    fenetre2.geometry("400x600")
    page_base = Frame(fenetre2)
    Label(page_base, text="Numéro de compte", font=("Arial", 8, "bold")).place(relx=0.2, rely=0.1, anchor=CENTER)
    Label(page_base, text="Balance", font=("Arial", 8, "bold")).place(relx=0.5, rely=0.1, anchor=CENTER)
    Label(page_base, text="Mots de passes", font=("Arial", 8, "bold")).place(relx=0.8, rely=0.1, anchor=CENTER)
    y=0.15
    for numero,balance,mots_de_passe in liste:

        Label(page_base, text=numero, font=("Arial", 8)).place(relx=0.2, rely=y, anchor=CENTER)
        Label(page_base, text=balance, font=("Arial", 8)).place(relx=0.5, rely=y, anchor=CENTER)
        Label(page_base, text="***", font=("Arial", 8)).place(relx=0.8, rely=y, anchor=CENTER)
        y += 0.05




    def montrer_motdepasse():
        y=0.15
        for numero, balance, mots_de_passe in liste:
            Label(page_base, text=mots_de_passe, font=("Arial", 8)).place(relx=0.8, rely=y, anchor=CENTER)
            y+= 0.05
       



    Button(page_base,text="Show password", command=montrer_motdepasse ).place(relx=0.5, rely=0.8, anchor=CENTER)

    page_miseajour = Frame(fenetre2)
    def comfirmation():
        top = Toplevel(page_miseajour)  # lié à la fenêtre principale
        top.title("Comfirmation")
        top.geometry("300x100")
        top.resizable(0, 0)


        Button(top, text="Oui", width=8).place(relx=0.3, rely=0.8, anchor=CENTER)
        Button(top, text="Non", width=8, command=top.destroy).place(relx=0.7, rely=0.8, anchor=CENTER)

        Label(top, text="Êtes-vous sûr?",
              font=("Arial", 9, "bold"), wraplength=280).pack(pady=(8, 2))

    def afficher(page):
        page_base.pack_forget()
        page_miseajour.pack_forget()
        page.pack(fill=BOTH, expand=True)




    menu = Menu(fenetre2)
    menu.add_command(label="Mon Compte", command=lambda: afficher(page_base))
    menu.add_command(label="Virements", command=lambda: afficher(page_miseajour))
    menu.add_command(label="Fermer la session", command=fenetre2.destroy)


    fenetre2.config(menu=menu)
    fenetre2.mainloop()
###################################################### client #########################
def succes_virement(montant, destinataire):
    top = Toplevel(fenetre)
    top.title("Virement")
    top.geometry("300x100")
    top.resizable(0, 0)

    Button(top, text="OK", width=8, command=top.destroy).pack(side=BOTTOM, pady=5)

    Label(top, text="Virement effectué", font=("Arial", 9, "bold"), fg="green").pack(pady=(8, 2))
    Label(top, text=f"{montant} $ envoyé au compte {destinataire}", wraplength=280).pack()
def erreur_virement(message):
    top = Toplevel(fenetre)
    top.title("Erreur")
    top.geometry("300x100")
    top.resizable(0, 0)

    Button(top, text="OK", width=8, command=top.destroy).pack(side=BOTTOM, pady=5)

    Label(top, text="Virement refusé", font=("Arial", 9, "bold")).pack(pady=(8, 2))
    Label(top, text=message, wraplength=280).pack()
def session_client():
    fenetre1 = Toplevel(fenetre)
    fenetre1.title("Client")
    fenetre1.geometry("400x600")
    page_compte = Frame(fenetre1)
    Label(page_compte, text="Mon Compte", font=("Arial", 14, "bold")).pack(pady=10)
    label_solde = Label(page_compte)
    label_solde.pack()
    zone_chart = Frame(page_compte)
    zone_chart.pack()

    Label(page_compte, text="Historique", font=("Arial", 11, "bold")).pack(pady=(10, 2))   # MODIF : dans page_compte
    zone_histo = Frame(page_compte)                                                         # MODIF : dans page_compte
    zone_histo.pack()                                                                       # MODIF

    def rafraichir():
        solde = info_compte(Numero_compte)[0][0]
        label_solde.config(text=f"Solde : {solde} $")
        for w in zone_chart.winfo_children():
            w.destroy()
        chart(zone_chart, Numero_compte, solde, width=380, height=250).pack()

        for w in zone_histo.winfo_children():
            w.destroy()
        historique = info_compte(Numero_compte)[1]
        for i, (sender, receiver, amount, d) in enumerate(reversed(historique[-8:])):      # MODIF : 8 derniers pour tenir sous le graphique
            if sender == int(Numero_compte):
                fleche, autre, montant, couleur = "↑", receiver, f"-{amount} $", "red"
            else:
                fleche, autre, montant, couleur = "↓", sender, f"+{amount} $", "green"
            Label(zone_histo, text=fleche, fg=couleur, font=("Arial", 12, "bold")).grid(row=i, column=0, padx=5)
            Label(zone_histo, text=f"Compte {autre}", fg=couleur).grid(row=i, column=1, padx=5, sticky="w")
            Label(zone_histo, text=montant, fg=couleur, font=("Arial", 10, "bold")).grid(row=i, column=2, padx=5)
            Label(zone_histo, text=d[:16], fg="gray", font=("Arial", 8)).grid(row=i, column=3, padx=5)

    page_virement = Frame(fenetre1)
    Label(page_virement, text="Virements", font=("Arial", 14, "bold")).pack(pady=10)
    Label(page_virement, text="Numéro du destinataire").pack()
    champ3=Entry(page_virement)
    champ3.pack()
    Label(page_virement, text="Montant").pack()
    champ4 = Entry(page_virement)
    champ4.pack()
    def virment():
        message = transfert(champ3.get(), Numero_compte, champ4.get())
    if message != "Virement effectué":
        erreur_virement(message)
    else:
        jouer_son()                                            # AJOUT
        succes_virement(champ4.get(), champ3.get())
    rafraichir()
    Button(page_virement, text="Envoyer", command=virment).pack(pady=10)

    def afficher(page):
        page_compte.pack_forget()
        page_virement.pack_forget()
        page.pack(fill=BOTH, expand=True)                  # MODIF : ligne page_historique.pack_forget() supprimée

    menu = Menu(fenetre1)
    menu.add_command(label="Mon Compte", command=lambda: afficher(page_compte))
    menu.add_command(label="Virements", command=lambda: afficher(page_virement))
    # MODIF : entrée de menu "Historique" supprimée
    menu.add_command(label="Fermer la session", command=fenetre1.destroy)


    fenetre1.config(menu=menu)
    rafraichir()
    afficher(page_compte)

########### BOUCLE PRINCIPALES #####################################################
#console_debut()
#accueil()
session_Admin()





########### BOUCLE PRINCIPALES #####################################################
console_debut()
accueil()
