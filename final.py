# Participants : (écrivez vos noms ici)
from tkinter import *
from tkinter import ttk  # AJOUT : pour la liste déroulante (Combobox)

import sqlite3

import random

from datetime import datetime, date

try:
    import winsound
except ImportError:  # Mac / Linux
    winsound = None


def jouer_son():
    # petit son quand un virement réussit
    if winsound:
        winsound.Beep(1000, 120)
        winsound.Beep(1400, 180)
    else:
        fenetre.bell()


################ connexion base de donner #########

connexion = sqlite3.connect("banque.db")
cursor = connexion.cursor()

############## CREER SI PAS EXISTANT / SOLDE BASE DE DONNER #########################33
# pour transfert
cursor.execute("CREATE TABLE IF NOT EXISTS history (SENDER INTEGER, RECEIVER INTEGER, AMOUNT INTEGER, DATE)")

# table pour account (fictif = 1 quand le compte est créé par l'admin)
cursor.execute(
    "CREATE TABLE IF NOT EXISTS comptes (num_compte INTEGER, argent INTEGER, password TEXT, phrase_mot TEXT, fictif INTEGER DEFAULT 0)")
try:
    cursor.execute("ALTER TABLE comptes ADD COLUMN fictif INTEGER DEFAULT 0")  # ancienne base sans la colonne
except sqlite3.OperationalError:
    pass  # la colonne existe déjà
# table pour numeros account possible
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
    # menu de départ dans l'interpréteur (A = connexion, U = nouvel utilisateur)
    print("Bonjour :")
    print(" - Tapez A, pour vous connecter à l’Application.")
    if len(compte_num) > 0:  # AJOUT : U n'apparaît plus quand les 10 numéros sont pris
        print(" - Tapez U, pour un nouvel Utilisateur.")

    choix = ""
    while choix != "A" and choix != "U":
        choix = input()
        choix = choix.upper()
        if choix == "U" and len(compte_num) == 0:
            choix = ""  # AJOUT : la touche U ne marche plus
        if choix == "U":
            num_compte = random.choice(compte_num)
            compte_num.remove(num_compte)
            argent = random.randint(100, 500)
            print(f"Bienvenue, voici votre numéro de compte {num_compte} ")

            password = input("Choisissez votre mot de passe et pressez sur ENTRÉE : ")
            while len(password) != 3:  # AJOUT : exactement 3 caractères
                password = input("Le mot de passe doit avoir exactement 3 caractères, réessayez : ")
            password_conf = input("Confirmez votre mot de passe puis pressez sur ENTRÉE : ")
            while password_conf != password:
                password_conf = input("Les mots de passe ne correspondent pas, réessayez : ")
            print("Indiquez une phrase pour vous rappeler du mot de passe et pressez sur ENTRÉE.")
            phrase_mot = input()

            # Base de données METTRE LES INFOS RECOLTER
            cursor.execute("DELETE FROM numeros_restants WHERE numero = ?", (num_compte,))
            cursor.execute("INSERT INTO comptes(num_compte, argent, password, phrase_mot) VALUES (?, ?, ?, ?)",
                           (num_compte, argent, password, phrase_mot))
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
    # vrai si le numéro de compte et le mot de passe correspondent
    try:
        numero_compte = int(numero_compte)
    except ValueError:  # AJOUT : le numéro n'est pas un nombre
        return False
    conn = sqlite3.connect("banque.db")
    curs = conn.cursor()

    curs.execute("SELECT password FROM comptes WHERE num_compte = ?", (numero_compte,))
    resultat = curs.fetchone()  # (mot_de_passe,) ou None si le compte n'existe pas
    conn.close()

    if resultat is None:
        return False  # compte inexistant
    return resultat[0] == mots_depasses

    ############## Recolte numeros ###########


def verification_mdp_admin(numero_compte, mots_depasses):
    # vrai si l'identifiant et le mot de passe admin sont bons
    return numero_compte == nom_adm and password_adm == mots_depasses


def Motsdepasses_oublié():
    # MODIF : le numéro et la phrase de rappel sont demandés dans l'interpréteur
    numero = input("Numéro de compte : ")
    phrase = input("Phrase de rappel : ")
    try:
        numero = int(numero)
    except ValueError:  # numéro pas un nombre
        print("Vous n'avez pas de compte client")
        return

    conn = sqlite3.connect("banque.db")
    curs = conn.cursor()
    curs.execute("SELECT password FROM comptes WHERE num_compte = ? AND phrase_mot = ?", (numero, phrase))
    resultat = curs.fetchone()  # (mot_de_passe,) ou None
    conn.close()

    if resultat is None:
        print("Numéro de compte ou phrase de rappel incorrect")
    else:
        print("Votre mot de passe :", resultat[0])


def info_compte(numero_compte):
    # retourne le solde et l'historique d'un compte
    numero_compte = int(numero_compte)
    conn = sqlite3.connect("banque.db")
    curs = conn.cursor()
    curs.execute("SELECT argent FROM comptes WHERE num_compte = ?", (numero_compte,))
    solde = curs.fetchone()  # (argent,) ou None si le compte n'existe pas
    curs.execute("SELECT SENDER, RECEIVER, AMOUNT, DATE FROM history "
                 "WHERE SENDER = ? OR RECEIVER = ? ORDER BY rowid",
                 (numero_compte, numero_compte))
    historique = curs.fetchall()  # liste de (SENDER, RECEIVER, AMOUNT, DATE)
    conn.close()
    return (solde, historique)


def liste_destinataires(sender):
    # AJOUT : comptes réels (pas fictifs) sauf soi-même
    conn = sqlite3.connect("banque.db")
    curs = conn.cursor()
    curs.execute("SELECT num_compte FROM comptes WHERE fictif = 0 AND num_compte != ? ORDER BY num_compte",
                 (int(sender),))
    resultat = [ligne[0] for ligne in curs.fetchall()]
    conn.close()
    return resultat


def transfert(receiver, sender, amount):
    # vérifie le virement puis met à jour les soldes et l'historique
    if not (str(receiver).isdigit() and str(amount).isdigit()):
        return "Numéro ou montant invalide"
    receiver, sender, amount = int(receiver), int(sender), int(amount)

    if receiver == sender:
        return "Vous ne pouvez pas vous envoyer de l'argent"
    if amount <= 0:
        return "Le montant doit être positif"
    if receiver not in liste_destinataires(sender):  # MODIF : seulement les comptes réels
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
    # l'admin change le solde d'un compte
    conn = sqlite3.connect("banque.db")
    curs = conn.cursor()
    curs.execute("UPDATE comptes SET argent = ? WHERE num_compte = ?",
                 (int(nouvelle_balance), int(numero_compte)))
    conn.commit()
    ok = curs.rowcount > 0
    conn.close()
    return ok


def modifier_mots_passe(numero_compte, nouveau_mdp):
    # change le mot de passe d'un compte
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
    # l'admin supprime un compte
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


def ajouter_compte_fictif():
    # AJOUT : l'admin reçoit un nouveau compte fictif (s'il reste un numéro libre)
    if len(compte_num) == 0:
        print("Plus aucun numéro de compte disponible.")
        return False
    num_compte = random.choice(compte_num)
    compte_num.remove(num_compte)
    argent = random.randint(100, 500)
    password = "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=3))  # 3 caractères au hasard
    conn = sqlite3.connect("banque.db")
    curs = conn.cursor()
    curs.execute("DELETE FROM numeros_restants WHERE numero = ?", (num_compte,))
    curs.execute("INSERT INTO comptes(num_compte, argent, password, phrase_mot, fictif) VALUES (?, ?, ?, ?, 1)",
                 (num_compte, argent, password, "fictif"))
    conn.commit()
    conn.close()
    return True


################################################### graphique ##########################################


def chart(parent, compte, actuel, width=500, height=300):
    # dessine la courbe du solde du compte dans un Canvas
    compte = int(compte)
    historique = info_compte(compte)[1]  # (SENDER, RECEIVER, AMOUNT, DATE)

    # On remonte le temps à partir du solde actuel
    points = [{"date": datetime.now(), "y": actuel}]
    solde = actuel
    for sender, receiver, amount, d in reversed(historique):
        points.append({"date": d, "y": solde})  # solde après ce virement
        solde += amount if sender == compte else -amount  # solde avant ce virement
    if historique:
        points.append({"date": historique[0][3], "y": solde})  # solde de départ
    points.reverse()  # ordre chronologique

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
        # transforme le texte de la base en vraie date
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
        # position x d'une date
        if start == end:
            return margin_left + graph_width / 2
        return margin_left + (
                (d - start).total_seconds() /
                (end - start).total_seconds()
        ) * graph_width

    def py(y):
        # position y d'un solde
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
    # fenêtre d'erreur quand la connexion ne marche pas
    top = Toplevel(fenetre)  # lié à la fenêtre principale
    top.title("Erreur")
    top.geometry("300x100")
    top.resizable(0, 0)

    # le bouton est empaqueté en premier pour rester tout en bas
    Button(top, text="OK", width=8, command=top.destroy).pack(side=BOTTOM, pady=5)

    Label(top, text="Renseignements d'ouverture de session erronés",
          font=("Arial", 9, "bold"), wraplength=280).pack(pady=(8, 2))
    Label(top, text="Veuillez vérifier vos données de connexion et réessayer",
          wraplength=280).pack()


def rouvrir_accueil():
    # AJOUT : on vide les champs et on réaffiche l'écran 1
    champ.delete(0, END)
    champ2.delete(0, END)
    fenetre.deiconify()


def accueil():
    # écran 1 : connexion client / admin
    global fenetre, Numero_compte, Admin, champ, champ2
    fenetre = Tk()
    fenetre.title("Accueil")
    fenetre.geometry("400x600")
    fenetre.resizable(0, 0)  # AJOUT : taille non modifiable
    Label(fenetre, text="Banque Grasséenne").pack(pady=20)
    Label(fenetre, text="Type de connexion").pack()
    Admin = StringVar()  # variable Tkinter, pas un booléen
    Admin.set("client")

    def désactiver():
        # grise le bouton "mot de passe oublié" en mode admin
        if Admin.get() == "admin":
            Bouton2.config(state="disabled")  # bouton grisé, non cliquable
        else:
            Bouton2.config(state="normal")

    Radiobutton(fenetre, text="Admin", variable=Admin, value="admin", command=désactiver).pack(anchor=CENTER)
    Radiobutton(fenetre, text="Client", variable=Admin, value="client", command=désactiver).pack(anchor=CENTER)

    Label(fenetre, text="Numéro de compte").pack(pady=10)
    champ = Entry(fenetre)
    champ.pack(pady=10)
    Numero_compte = champ.get()

    # MODIF : le champ du mot de passe est visible tout de suite (3 caractères max, caché par des *)
    def max3(texte):
        # refuse un 4e caractère
        return len(texte) <= 3

    Label(fenetre, text="Mots de passes").place(relx=0.5, rely=0.4, anchor=CENTER)
    champ2 = Entry(fenetre, show="*", validate="key", validatecommand=(fenetre.register(max3), "%P"))
    champ2.place(relx=0.5, rely=0.45, anchor=CENTER)

    champ.bind("<Return>", lambda event: champ2.focus())  # ENTRÉE passe au mot de passe

    def connexion():
        # vérifie les infos puis ouvre l'écran client ou admin
        global Numero_compte
        if Admin.get() == "admin":
            if verification_mdp_admin(champ.get(), champ2.get()):
                fenetre.withdraw()  # AJOUT : on cache l'écran 1
                session_Admin()
            else:
                erreur_connexion()
        elif Admin.get() == "client":
            if verification_mdp_client(champ.get(), champ2.get()):
                Numero_compte = champ.get()  # <-- ajouté
                fenetre.withdraw()  # AJOUT : on cache l'écran 1
                session_client()
            else:
                erreur_connexion()

    Bouton1 = Button(fenetre, text="Ouvrir une session", command=connexion)
    Bouton1.place(relx=0.5, rely=0.6, anchor=CENTER)
    Bouton2 = Button(fenetre, text="Mot de passe oublié ?", command=Motsdepasses_oublié)
    Bouton2.place(relx=0.5, rely=0.67, anchor=CENTER)

    # AJOUT : animation d'une pièce qui rebondit (Canvas + after)
    canevas = Canvas(fenetre, width=300, height=50, highlightthickness=0)
    canevas.place(relx=0.5, rely=0.82, anchor=CENTER)
    piece = canevas.create_oval(5, 10, 35, 40, fill="gold", outline="orange")
    signe = canevas.create_text(20, 25, text="$", font=("Arial", 12, "bold"))
    vitesse = 4

    def animer():
        # déplace la pièce et la fait rebondir sur les bords
        nonlocal vitesse
        canevas.move(piece, vitesse, 0)
        canevas.move(signe, vitesse, 0)
        x1, y1, x2, y2 = canevas.coords(piece)
        if x2 >= 300 or x1 <= 0:
            vitesse = -vitesse
        fenetre.after(30, animer)

    # AJOUT : horloge en direct (timer avec after)
    label_heure = Label(fenetre, font=("Arial", 9))
    label_heure.place(relx=0.5, rely=0.93, anchor=CENTER)

    def horloge():
        # met l'heure à jour chaque seconde
        label_heure.config(text=datetime.now().strftime("%d/%m/%Y  %H:%M:%S"))
        fenetre.after(1000, horloge)

    animer()
    horloge()
    fenetre.mainloop()


#######################################ADMIN#######################################################3

def session_Admin():
    # écran 3 : interface administrateur
    ajouter_compte_fictif()  # AJOUT : un nouveau compte fictif à chaque session admin
    fenetre2 = Toplevel(fenetre)  # MODIF : Toplevel au lieu d'un 2e Tk()
    fenetre2.title("Admin")
    fenetre2.geometry("400x300")  # MODIF : 400x300 comme demandé
    fenetre2.resizable(0, 0)  # AJOUT : taille non modifiable
    page_base = Frame(fenetre2)
    page_miseajour = Frame(fenetre2)

    def rafraichir_base():
        # redessine la liste des comptes (page Base de données)
        for w in page_base.winfo_children():
            w.destroy()
        liste = recuperer_TOUTacoount()
        Label(page_base, text="Numéro de compte", font=("Arial", 8, "bold")).place(relx=0.2, rely=0.1, anchor=CENTER)
        Label(page_base, text="Balance", font=("Arial", 8, "bold")).place(relx=0.5, rely=0.1, anchor=CENTER)
        Label(page_base, text="Mots de passes", font=("Arial", 8, "bold")).place(relx=0.8, rely=0.1, anchor=CENTER)
        y = 0.15
        for numero, balance, mots_de_passe in liste:
            Label(page_base, text=numero, font=("Arial", 8)).place(relx=0.2, rely=y, anchor=CENTER)
            Label(page_base, text=balance, font=("Arial", 8)).place(relx=0.5, rely=y, anchor=CENTER)
            Label(page_base, text="***", font=("Arial", 8)).place(relx=0.8, rely=y, anchor=CENTER)
            y += 0.06

        def montrer_motdepasse():
            # affiche les vrais mots de passe
            y = 0.15
            for numero, balance, mots_de_passe in liste:
                Label(page_base, text=mots_de_passe, font=("Arial", 8)).place(relx=0.8, rely=y, anchor=CENTER)
                y += 0.06

        Button(page_base, text="Show password", command=montrer_motdepasse).place(relx=0.5, rely=0.88, anchor=CENTER)

    # AJOUT : page Mise à jour (supprimer un compte ou modifier son solde)
    Label(page_miseajour, text="Mise à jour", font=("Arial", 14, "bold")).pack(pady=10)
    Label(page_miseajour, text="Compte à modifier").pack()
    combo = ttk.Combobox(page_miseajour, state="readonly")  # nouveau widget : liste déroulante
    combo.pack(pady=5)
    Label(page_miseajour, text="Nouveau solde ($)").pack()
    champ_solde = Entry(page_miseajour)
    champ_solde.pack(pady=5)
    label_msg = Label(page_miseajour, wraplength=380)
    label_msg.pack()

    def rafraichir_admin():
        # met à jour la liste des comptes et la liste déroulante
        rafraichir_base()
        combo["values"] = [ligne[0] for ligne in recuperer_TOUTacoount()]
        combo.set("")
        champ_solde.delete(0, END)

    def comfirmation(action):
        # MODIF : le bouton Oui lance l'action demandée
        top = Toplevel(page_miseajour)  # lié à la fenêtre principale
        top.title("Comfirmation")
        top.geometry("300x100")
        top.resizable(0, 0)

        def oui():
            action()
            top.destroy()

        Button(top, text="Oui", width=8, command=oui).place(relx=0.3, rely=0.8, anchor=CENTER)
        Button(top, text="Non", width=8, command=top.destroy).place(relx=0.7, rely=0.8, anchor=CENTER)

        Label(top, text="Êtes-vous sûr?",
              font=("Arial", 9, "bold"), wraplength=280).pack(pady=(8, 2))

    def changer_solde():
        # vérifie le compte et le solde puis demande confirmation
        try:
            numero = int(combo.get())
            solde = int(champ_solde.get())
            if solde < 0:
                raise ValueError
        except ValueError:  # aucun compte choisi ou solde pas valide
            label_msg.config(text="Choisissez un compte et un solde valide (0 ou plus)", fg="red")
            return

        def faire():
            modifier_balance(numero, solde)
            rafraichir_admin()
            label_msg.config(text=f"Solde du compte {numero} modifié", fg="green")

        comfirmation(faire)

    def effacer_compte():
        # vérifie le compte choisi puis demande confirmation
        try:
            numero = int(combo.get())
        except ValueError:  # aucun compte choisi
            label_msg.config(text="Choisissez un compte", fg="red")
            return

        def faire():
            supprimer_compte(numero)
            rafraichir_admin()
            label_msg.config(text=f"Compte {numero} supprimé", fg="green")

        comfirmation(faire)

    Button(page_miseajour, text="Modifier le solde", command=changer_solde).pack(pady=3)
    Button(page_miseajour, text="Supprimer le compte", command=effacer_compte).pack(pady=3)

    def afficher(page):
        # montre une seule page à la fois
        page_base.pack_forget()
        page_miseajour.pack_forget()
        page.pack(fill=BOTH, expand=True)

    def quitter():
        # ferme l'écran 3 et rouvre l'écran 1
        fenetre2.destroy()
        rouvrir_accueil()

    menu = Menu(fenetre2)
    menu.add_command(label="Base de données", command=lambda: afficher(page_base))  # MODIF : noms du menu
    menu.add_command(label="Mise à jour", command=lambda: afficher(page_miseajour))
    menu.add_command(label="Quitter", command=quitter)

    fenetre2.config(menu=menu)
    fenetre2.protocol("WM_DELETE_WINDOW", quitter)  # la croix fait pareil que Quitter
    rafraichir_admin()
    afficher(page_base)  # AJOUT : page affichée dès l'ouverture


###################################################### client #########################
def succes_virement(montant, destinataire):
    # fenêtre quand le virement a marché
    top = Toplevel(fenetre)
    top.title("Virement")
    top.geometry("300x100")
    top.resizable(0, 0)

    Button(top, text="OK", width=8, command=top.destroy).pack(side=BOTTOM, pady=5)

    Label(top, text="Virement effectué", font=("Arial", 9, "bold"), fg="green").pack(pady=(8, 2))
    Label(top, text=f"{montant} $ envoyé au compte {destinataire}", wraplength=280).pack()


def erreur_virement(message):
    # fenêtre quand le virement est refusé
    top = Toplevel(fenetre)
    top.title("Erreur")
    top.geometry("300x100")
    top.resizable(0, 0)

    Button(top, text="OK", width=8, command=top.destroy).pack(side=BOTTOM, pady=5)

    Label(top, text="Virement refusé", font=("Arial", 9, "bold")).pack(pady=(8, 2))
    Label(top, text=message, wraplength=280).pack()


def session_client():
    # écran 2 : interface client
    fenetre1 = Toplevel(fenetre)
    fenetre1.title("Client")
    fenetre1.geometry("400x600")
    fenetre1.resizable(0, 0)  # AJOUT : taille non modifiable
    Label(fenetre1, text="Banque Grasséenne", font=("Arial", 10, "bold")).pack(pady=5)  # AJOUT : nom de la banque
    page_compte = Frame(fenetre1)
    Label(page_compte, text="Mon Compte", font=("Arial", 14, "bold")).pack(pady=10)
    label_num = Label(page_compte)  # AJOUT : numéro de compte
    label_num.pack()
    label_solde = Label(page_compte)
    label_solde.pack()
    label_nb = Label(page_compte)  # AJOUT : nombre de virements effectués
    label_nb.pack()
    zone_chart = Frame(page_compte)
    zone_chart.pack()

    Label(page_compte, text="Historique", font=("Arial", 11, "bold")).pack(pady=(10, 2))  # MODIF : dans page_compte
    zone_histo = Frame(page_compte)  # MODIF : dans page_compte
    zone_histo.pack()  # MODIF

    def rafraichir():
        # met à jour le solde, le graphique, l'historique et la liste des bénéficiaires
        info = info_compte(Numero_compte)
        solde = info[0][0]
        historique = info[1]
        nb_virements = len([h for h in historique if h[0] == int(Numero_compte)])  # virements envoyés
        label_num.config(text=f"Numéro de compte : {Numero_compte}")
        label_solde.config(text=f"Solde : {solde} $")
        label_nb.config(text=f"Virements effectués : {nb_virements}")
        for w in zone_chart.winfo_children():
            w.destroy()
        chart(zone_chart, Numero_compte, solde, width=380, height=220).pack()  # MODIF : un peu plus petit

        for w in zone_histo.winfo_children():
            w.destroy()
        for i, (sender, receiver, amount, d) in enumerate(
                reversed(historique[-6:])):  # MODIF : 6 derniers pour tenir sous le graphique
            if sender == int(Numero_compte):
                fleche, autre, montant, couleur = "↑", receiver, f"-{amount} $", "red"
            else:
                fleche, autre, montant, couleur = "↓", sender, f"+{amount} $", "green"
            Label(zone_histo, text=fleche, fg=couleur, font=("Arial", 12, "bold")).grid(row=i, column=0, padx=5)
            Label(zone_histo, text=f"Compte {autre}", fg=couleur).grid(row=i, column=1, padx=5, sticky="w")
            Label(zone_histo, text=montant, fg=couleur, font=("Arial", 10, "bold")).grid(row=i, column=2, padx=5)
            Label(zone_histo, text=d[:16], fg="gray", font=("Arial", 8)).grid(row=i, column=3, padx=5)

        # AJOUT : boutons radio avec les comptes disponibles
        for w in zone_dest.winfo_children():
            w.destroy()
        dest.set("")
        destinataires = liste_destinataires(Numero_compte)
        if len(destinataires) == 0:
            Label(zone_dest, text="Aucun autre compte disponible").pack()
        for n in destinataires:
            Radiobutton(zone_dest, text=f"Compte {n}", variable=dest, value=str(n)).pack(anchor="w")

    page_virement = Frame(fenetre1)
    Label(page_virement, text="Virements", font=("Arial", 14, "bold")).pack(pady=10)
    Label(page_virement, text="Choisissez le bénéficiaire").pack()  # MODIF : radio au lieu d'un champ à taper
    dest = StringVar()  # numéro du bénéficiaire choisi
    zone_dest = Frame(page_virement)
    zone_dest.pack(pady=5)
    Label(page_virement, text="Montant ($)").pack()
    champ4 = Entry(page_virement)
    champ4.pack()

    def virment():
        # MODIF : indentation corrigée, tout est dans la fonction
        if dest.get() == "":
            erreur_virement("Choisissez un bénéficiaire")
            return
        message = transfert(dest.get(), Numero_compte, champ4.get())  # MODIF : message en minuscule
        if message != "Virement effectué":
            erreur_virement(message)
        else:
            jouer_son()  # AJOUT
            succes_virement(champ4.get(), dest.get())
        champ4.delete(0, END)
        rafraichir()

    Button(page_virement, text="Envoyer", command=virment).pack(pady=10)

    def afficher(page):
        # montre une seule page à la fois
        page_compte.pack_forget()
        page_virement.pack_forget()
        page.pack(fill=BOTH, expand=True)  # MODIF : ligne page_historique.pack_forget() supprimée

    def fermer():
        # ferme l'écran 2 et rouvre l'écran 1
        fenetre1.destroy()
        rouvrir_accueil()

    menu = Menu(fenetre1)
    menu.add_command(label="Mon Compte", command=lambda: afficher(page_compte))
    menu.add_command(label="Virements", command=lambda: afficher(page_virement))
    # MODIF : entrée de menu "Historique" supprimée
    menu.add_command(label="Fermer la session", command=fermer)

    fenetre1.config(menu=menu)
    fenetre1.protocol("WM_DELETE_WINDOW", fermer)  # la croix fait pareil que Fermer la session
    rafraichir()
    afficher(page_compte)


########### BOUCLE PRINCIPALES #####################################################
# console_debut()
# accueil()

########### BOUCLE PRINCIPALES #####################################################
console_debut()
accueil()
