
from tkinter import *
from tkinter import ttk
import tkinter.font as tkfont

import sqlite3

import random

from datetime import datetime, date

try:
    import winsound
except ImportError:
    winsound = None

# Les 3 polices utilisées dans tout le programme
POLICE_TEXTE = "Arial"
POLICE_TITRE = "Times New Roman"
POLICE_CHIFFRES = "Courier New"


def jouer_son():
    # petit son quand un virement réussit
    if winsound:
        winsound.Beep(1000, 120)
        winsound.Beep(1400, 180)
    else:
        fenetre.bell()


################ connexion à la base de données #########

connexion = sqlite3.connect("banque.db")
cursor = connexion.cursor()

############## création des tables si elles n'existent pas #########################

# table des virements
cursor.execute("CREATE TABLE IF NOT EXISTS history (SENDER INTEGER, RECEIVER INTEGER, AMOUNT INTEGER, DATE)")

# table des comptes (fictif = 1 quand le compte est créé par l'admin)
cursor.execute(
    "CREATE TABLE IF NOT EXISTS comptes (num_compte INTEGER, argent INTEGER, password TEXT, phrase_mot TEXT, fictif INTEGER DEFAULT 0)")
try:
    cursor.execute("ALTER TABLE comptes ADD COLUMN fictif INTEGER DEFAULT 0")  # vieille base sans la colonne
except sqlite3.OperationalError:
    pass  # la colonne existe déjà

# deux comptes ne peuvent jamais avoir le même numéro
try:
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS numero_unique ON comptes (num_compte)")
except sqlite3.Error:
    pass  # une vieille base contient déjà des doublons

# table des numéros de compte encore libres
cursor.execute("CREATE TABLE IF NOT EXISTS numeros_restants (numero INTEGER)")

########################### NUMÉROS DE COMPTE #################################
# Première fois seulement : on remplit la liste des numéros (101 à 110)
cursor.execute("SELECT COUNT(*) FROM numeros_restants")
nb_restants = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM comptes")
nb_comptes = cursor.fetchone()[0]
if nb_restants == 0 and nb_comptes == 0:
    for n in range(101, 111):
        cursor.execute("INSERT INTO numeros_restants VALUES (?)", (n,))
    connexion.commit()

# La liste des numéros libres vient de la base
cursor.execute("SELECT numero FROM numeros_restants")
compte_num = [ligne[0] for ligne in cursor.fetchall()]


def tirer_numero():
    # choisit un numéro libre au hasard et vérifie qu'aucun compte ne l'a déjà
    # s'il est déjà pris, on le jette et on en tire un autre
    # retourne None s'il n'y a plus de numéro disponible
    while len(compte_num) > 0:
        num = random.choice(compte_num)
        compte_num.remove(num)
        conn = sqlite3.connect("banque.db")
        curs = conn.cursor()
        curs.execute("SELECT COUNT(*) FROM comptes WHERE num_compte = ?", (num,))
        deja_pris = curs.fetchone()[0] > 0
        if deja_pris:
            curs.execute("DELETE FROM numeros_restants WHERE numero = ?", (num,))
            conn.commit()
        conn.close()
        if not deja_pris:
            return num
    return None


########### CONSOLE ################

def console_debut():
    # menu de départ dans l'interpréteur (A = connexion, U = nouvel utilisateur)
    print("Bonjour :")
    print(" - Tapez A, pour vous connecter à l’Application.")
    if len(compte_num) > 0:  # quand les 10 numéros sont pris, U n'est plus proposé
        print(" - Tapez U, pour un nouvel Utilisateur.")

    choix = ""
    while choix != "A" and choix != "U":
        choix = input()
        choix = choix.upper()
        if choix == "U" and len(compte_num) == 0:
            choix = ""  # la touche U ne marche plus
        if choix == "U":
            num_compte = tirer_numero()
            if num_compte is None:
                print("Plus aucun numéro de compte disponible.")
                choix = ""
            else:
                argent = random.randint(100, 500)
                print(f"Bienvenue, voici votre numéro de compte {num_compte} ")

                password = input("Choisissez votre mot de passe et pressez sur ENTRÉE : ")
                while len(password) != 3:  # exactement 3 caractères
                    password = input("Le mot de passe doit avoir exactement 3 caractères, réessayez : ")
                password_conf = input("Confirmez votre mot de passe puis pressez sur ENTRÉE : ")
                while password_conf != password:
                    password_conf = input("Les mots de passe ne correspondent pas, réessayez : ")
                print("Indiquez une phrase pour vous rappeler du mot de passe et pressez sur ENTRÉE.")
                phrase_mot = input()

                # on enregistre les infos dans la base de données
                cursor.execute("DELETE FROM numeros_restants WHERE numero = ?", (num_compte,))
                cursor.execute("INSERT INTO comptes(num_compte, argent, password, phrase_mot) VALUES (?, ?, ?, ?)",
                               (num_compte, argent, password, phrase_mot))
                connexion.commit()

    connexion.close()


######### MOT DE PASSE ADMIN ###############################################

password_adm = "123"
nom_adm = "adm"


############################ FONCTIONS DE LA BASE DE DONNÉES ####################

def verification_mdp_client(numero_compte, mdp):
    # vrai si le numéro de compte et le mot de passe correspondent
    try:
        numero_compte = int(numero_compte)
    except ValueError:  # le numéro n'est pas un nombre
        return False
    conn = sqlite3.connect("banque.db")
    curs = conn.cursor()

    curs.execute("SELECT password FROM comptes WHERE num_compte = ?", (numero_compte,))
    resultat = curs.fetchone()  # (mot_de_passe,) ou None si le compte n'existe pas
    conn.close()

    if resultat is None:
        return False  # compte inexistant
    return resultat[0] == mdp


def verification_mdp_admin(identifiant, mdp):
    # vrai si l'identifiant et le mot de passe admin sont bons
    return identifiant == nom_adm and password_adm == mdp


def mot_de_passe_oublie():
    # le numéro et la phrase de rappel sont demandés dans l'interpréteur
    numero = input("Numéro de compte : ")
    phrase = input("Phrase de rappel : ")
    try:
        numero = int(numero)
    except ValueError:  # le numéro n'est pas un nombre
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
    # les comptes réels (pas fictifs), sauf soi-même
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
    if receiver not in liste_destinataires(sender):  # seulement les comptes réels
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


def modifier_mot_de_passe(numero_compte, nouveau_mdp):
    # change le mot de passe d'un compte
    conn = sqlite3.connect("banque.db")
    curs = conn.cursor()
    curs.execute("UPDATE comptes SET password = ? WHERE num_compte = ?",
                 (nouveau_mdp, int(numero_compte)))
    conn.commit()
    ok = curs.rowcount > 0
    conn.close()
    return ok


def recuperer_tous_les_comptes():
    # retourne une liste de tuples : [(num_compte, argent, password), ...]
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
        # le numéro redevient libre et son historique est effacé
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
    # l'admin reçoit un nouveau compte fictif (s'il reste un numéro libre)
    num_compte = tirer_numero()
    if num_compte is None:
        print("Plus aucun numéro de compte disponible.")
        return False
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

    # minimum et maximum du graphique
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
        anchor="e",
        font=(POLICE_CHIFFRES, 9)
    )

    canvas.create_text(
        margin_left - 10, py(plus_haut),
        text=str(plus_haut),
        anchor="e",
        font=(POLICE_CHIFFRES, 9)
    )

    # Valeur actuelle
    if actuel != plus_bas and actuel != plus_haut:
        canvas.create_text(
            margin_left - 10, py(actuel),
            text=str(actuel),
            anchor="e",
            fill="blue",
            font=(POLICE_CHIFFRES, 9, "bold")
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
            font=(POLICE_CHIFFRES, 8)
        )

    # La courbe
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
    top = Toplevel(fenetre)
    top.title("Erreur")
    top.geometry("300x100")
    top.resizable(0, 0)

    # le bouton est mis en premier pour rester tout en bas
    Button(top, text="OK", width=8, command=top.destroy).pack(side=BOTTOM, pady=5)

    Label(top, text="Renseignements d'ouverture de session erronés",
          font=(POLICE_TEXTE, 9, "bold"), wraplength=280).pack(pady=(8, 2))
    Label(top, text="Veuillez vérifier vos données de connexion et réessayer",
          wraplength=280).pack()


def rouvrir_accueil():
    # on vide les champs, on recache le mot de passe et on réaffiche l'écran 1
    champ.delete(0, END)
    champ2.delete(0, END)
    label_mdp.place_forget()
    champ2.place_forget()
    fenetre.deiconify()
    champ.focus()


def accueil():
    # écran 1 : connexion client / admin
    global fenetre, Admin, champ, champ2, label_mdp
    fenetre = Tk()
    fenetre.title("Accueil")
    fenetre.geometry("400x600")
    fenetre.resizable(0, 0)  # taille non modifiable

    # Les widgets sans police précise prennent la police par défaut de Tkinter.
    # On la remplace pour n'avoir que nos 3 polices dans tout le programme.
    for nom in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont",
                "TkCaptionFont", "TkSmallCaptionFont", "TkIconFont", "TkTooltipFont"):
        tkfont.nametofont(nom).configure(family=POLICE_TEXTE)
    tkfont.nametofont("TkFixedFont").configure(family=POLICE_CHIFFRES)

    Label(fenetre, text="Banque Grasséenne", font=(POLICE_TITRE, 16, "bold")).pack(pady=20)
    Label(fenetre, text="Type de connexion").pack()
    Admin = StringVar()  # variable Tkinter, pas un booléen
    Admin.set("client")

    def desactiver():
        # grise le bouton "mot de passe oublié" en mode admin
        if Admin.get() == "admin":
            Bouton2.config(state="disabled")
        else:
            Bouton2.config(state="normal")

    Radiobutton(fenetre, text="Admin", variable=Admin, value="admin", command=desactiver).pack(anchor=CENTER)
    Radiobutton(fenetre, text="Client", variable=Admin, value="client", command=desactiver).pack(anchor=CENTER)

    Label(fenetre, text="Numéro de compte").pack(pady=10)
    champ = Entry(fenetre)
    champ.pack(pady=10)

    def max3(texte):
        # refuse un 4e caractère
        return len(texte) <= 3

    # Le mot de passe est caché grâce à show="*" : le texte tapé est bien gardé
    # dans le champ (champ2.get() le retrouve) mais Tkinter affiche des * à la place.
    # validate="key" appelle max3 à chaque touche pour limiter à 3 caractères.
    # On les crée ici mais on ne les place pas : ils apparaissent après ENTRÉE.
    label_mdp = Label(fenetre, text="Mot de passe")
    champ2 = Entry(fenetre, show="*", validate="key", validatecommand=(fenetre.register(max3), "%P"))

    def montrer_mdp(event=None):
        # affiche le champ du mot de passe et met le curseur dedans
        label_mdp.place(relx=0.5, rely=0.4, anchor=CENTER)
        champ2.place(relx=0.5, rely=0.45, anchor=CENTER)
        champ2.focus()

    champ.bind("<Return>", montrer_mdp)  # ENTRÉE dans le numéro de compte

    def ouvrir_session():
        # vérifie les infos puis ouvre l'écran client ou admin
        global Numero_compte
        if champ2.winfo_manager() == "":  # le mot de passe n'est pas encore affiché
            montrer_mdp()
            return
        if Admin.get() == "admin":
            if verification_mdp_admin(champ.get(), champ2.get()):
                fenetre.withdraw()  # on cache l'écran 1
                session_Admin()
            else:
                erreur_connexion()
        elif Admin.get() == "client":
            if verification_mdp_client(champ.get(), champ2.get()):
                Numero_compte = champ.get()
                fenetre.withdraw()  # on cache l'écran 1
                session_client()
            else:
                erreur_connexion()

    Bouton1 = Button(fenetre, text="Ouvrir une session", command=ouvrir_session)
    Bouton1.place(relx=0.5, rely=0.6, anchor=CENTER)
    Bouton2 = Button(fenetre, text="Mot de passe oublié ?", command=mot_de_passe_oublie)
    Bouton2.place(relx=0.5, rely=0.67, anchor=CENTER)

    # animation d'une pièce qui rebondit (Canvas + after)
    canevas = Canvas(fenetre, width=300, height=50, highlightthickness=0)
    canevas.place(relx=0.5, rely=0.82, anchor=CENTER)
    piece = canevas.create_oval(5, 10, 35, 40, fill="gold", outline="orange")
    signe = canevas.create_text(20, 25, text="$", font=(POLICE_CHIFFRES, 12, "bold"))
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

    # horloge en direct (timer avec after)
    label_heure = Label(fenetre, font=(POLICE_CHIFFRES, 9))
    label_heure.place(relx=0.5, rely=0.93, anchor=CENTER)

    def horloge():
        # met l'heure à jour chaque seconde
        label_heure.config(text=datetime.now().strftime("%d/%m/%Y  %H:%M:%S"))
        fenetre.after(1000, horloge)

    animer()
    horloge()
    fenetre.mainloop()


#######################################ADMIN#######################################################

def session_Admin():
    # écran 3 : interface administrateur
    ajouter_compte_fictif()  # un nouveau compte fictif à chaque session admin
    fenetre2 = Toplevel(fenetre)
    fenetre2.title("Admin")
    fenetre2.geometry("400x300")
    fenetre2.resizable(0, 0)  # taille non modifiable
    page_base = Frame(fenetre2)
    page_miseajour = Frame(fenetre2)

    def rafraichir_base():
        # redessine la liste des comptes (page Base de données)
        for w in page_base.winfo_children():
            w.destroy()
        liste = recuperer_tous_les_comptes()
        Label(page_base, text="Numéro de compte", font=(POLICE_TEXTE, 8, "bold")).place(relx=0.2, rely=0.1, anchor=CENTER)
        Label(page_base, text="Balance", font=(POLICE_TEXTE, 8, "bold")).place(relx=0.5, rely=0.1, anchor=CENTER)
        Label(page_base, text="Mot de passe", font=(POLICE_TEXTE, 8, "bold")).place(relx=0.8, rely=0.1, anchor=CENTER)

        labels_mdp = []  # (label, vrai mot de passe) pour chaque compte
        y = 0.15
        for numero, balance, mdp in liste:
            Label(page_base, text=numero, font=(POLICE_CHIFFRES, 9)).place(relx=0.2, rely=y, anchor=CENTER)
            Label(page_base, text=balance, font=(POLICE_CHIFFRES, 9)).place(relx=0.5, rely=y, anchor=CENTER)
            label = Label(page_base, text="***", font=(POLICE_CHIFFRES, 9))
            label.place(relx=0.8, rely=y, anchor=CENTER)
            labels_mdp.append((label, mdp))
            y += 0.06

        visible = False  # au début les mots de passe sont cachés

        def changer_affichage():
            # un seul bouton : Show password affiche, Hide password cache
            nonlocal visible
            visible = not visible
            for label, mdp in labels_mdp:
                if visible:
                    label.config(text=mdp)
                else:
                    label.config(text="***")
            if visible:
                bouton_mdp.config(text="Hide password")
            else:
                bouton_mdp.config(text="Show password")

        bouton_mdp = Button(page_base, text="Show password", command=changer_affichage)
        bouton_mdp.place(relx=0.5, rely=0.88, anchor=CENTER)

    # page Mise à jour (supprimer un compte ou modifier son solde)
    Label(page_miseajour, text="Mise à jour", font=(POLICE_TITRE, 14, "bold")).pack(pady=10)
    Label(page_miseajour, text="Compte à modifier").pack()
    combo = ttk.Combobox(page_miseajour, state="readonly")  # liste déroulante
    combo.pack(pady=5)
    Label(page_miseajour, text="Nouveau solde ($)").pack()
    champ_solde = Entry(page_miseajour)
    champ_solde.pack(pady=5)
    label_msg = Label(page_miseajour, wraplength=380)
    label_msg.pack()

    def rafraichir_admin():
        # met à jour la liste des comptes et la liste déroulante
        rafraichir_base()
        combo["values"] = [ligne[0] for ligne in recuperer_tous_les_comptes()]
        combo.set("")
        champ_solde.delete(0, END)

    def confirmation(action):
        # le bouton Oui lance l'action demandée
        top = Toplevel(page_miseajour)
        top.title("Confirmation")
        top.geometry("300x100")
        top.resizable(0, 0)

        def oui():
            action()
            top.destroy()

        Button(top, text="Oui", width=8, command=oui).place(relx=0.3, rely=0.8, anchor=CENTER)
        Button(top, text="Non", width=8, command=top.destroy).place(relx=0.7, rely=0.8, anchor=CENTER)

        Label(top, text="Êtes-vous sûr ?",
              font=(POLICE_TEXTE, 9, "bold"), wraplength=280).pack(pady=(8, 2))

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

        confirmation(faire)

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

        confirmation(faire)

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
    menu.add_command(label="Base de données", command=lambda: afficher(page_base))
    menu.add_command(label="Mise à jour", command=lambda: afficher(page_miseajour))
    menu.add_command(label="Quitter", command=quitter)

    fenetre2.config(menu=menu)
    fenetre2.protocol("WM_DELETE_WINDOW", quitter)  # la croix fait pareil que Quitter
    rafraichir_admin()
    afficher(page_base)  # page affichée dès l'ouverture


###################################################### client #########################
def succes_virement(montant, destinataire):
    # fenêtre quand le virement a marché
    top = Toplevel(fenetre)
    top.title("Virement")
    top.geometry("300x100")
    top.resizable(0, 0)

    Button(top, text="OK", width=8, command=top.destroy).pack(side=BOTTOM, pady=5)

    Label(top, text="Virement effectué", font=(POLICE_TEXTE, 9, "bold"), fg="green").pack(pady=(8, 2))
    Label(top, text=f"{montant} $ envoyé au compte {destinataire}", wraplength=280).pack()


def erreur_virement(message):
    # fenêtre quand le virement est refusé
    top = Toplevel(fenetre)
    top.title("Erreur")
    top.geometry("300x100")
    top.resizable(0, 0)

    Button(top, text="OK", width=8, command=top.destroy).pack(side=BOTTOM, pady=5)

    Label(top, text="Virement refusé", font=(POLICE_TEXTE, 9, "bold")).pack(pady=(8, 2))
    Label(top, text=message, wraplength=280).pack()


def session_client():
    # écran 2 : interface client
    fenetre1 = Toplevel(fenetre)
    fenetre1.title("Client")
    fenetre1.geometry("400x600")
    fenetre1.resizable(0, 0)  # taille non modifiable
    Label(fenetre1, text="Banque Grasséenne", font=(POLICE_TITRE, 12, "bold")).pack(pady=5)
    page_compte = Frame(fenetre1)
    Label(page_compte, text="Mon Compte", font=(POLICE_TITRE, 14, "bold")).pack(pady=10)
    label_num = Label(page_compte, font=(POLICE_CHIFFRES, 10))  # numéro de compte
    label_num.pack()
    label_solde = Label(page_compte, font=(POLICE_CHIFFRES, 10))
    label_solde.pack()
    label_nb = Label(page_compte, font=(POLICE_CHIFFRES, 10))  # nombre de virements effectués
    label_nb.pack()
    zone_chart = Frame(page_compte)
    zone_chart.pack()

    Label(page_compte, text="Historique", font=(POLICE_TITRE, 12, "bold")).pack(pady=(10, 2))
    zone_histo = Frame(page_compte)
    zone_histo.pack()

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
        chart(zone_chart, Numero_compte, solde, width=380, height=220).pack()

        for w in zone_histo.winfo_children():
            w.destroy()
        for i, (sender, receiver, amount, d) in enumerate(
                reversed(historique[-6:])):  # les 6 derniers pour tenir sous le graphique
            if sender == int(Numero_compte):
                fleche, autre, montant, couleur = "↑", receiver, f"-{amount} $", "red"
            else:
                fleche, autre, montant, couleur = "↓", sender, f"+{amount} $", "green"
            Label(zone_histo, text=fleche, fg=couleur, font=(POLICE_TEXTE, 12, "bold")).grid(row=i, column=0, padx=5)
            Label(zone_histo, text=f"Compte {autre}", fg=couleur).grid(row=i, column=1, padx=5, sticky="w")
            Label(zone_histo, text=montant, fg=couleur, font=(POLICE_CHIFFRES, 10, "bold")).grid(row=i, column=2, padx=5)
            Label(zone_histo, text=d[:16], fg="gray", font=(POLICE_CHIFFRES, 8)).grid(row=i, column=3, padx=5)

        # boutons radio avec les comptes disponibles
        for w in zone_dest.winfo_children():
            w.destroy()
        dest.set("")
        destinataires = liste_destinataires(Numero_compte)
        if len(destinataires) == 0:
            Label(zone_dest, text="Aucun autre compte disponible").pack()
        for n in destinataires:
            Radiobutton(zone_dest, text=f"Compte {n}", variable=dest, value=str(n)).pack(anchor="w")

    page_virement = Frame(fenetre1)
    Label(page_virement, text="Virements", font=(POLICE_TITRE, 14, "bold")).pack(pady=10)
    Label(page_virement, text="Choisissez le bénéficiaire").pack()
    dest = StringVar()  # numéro du bénéficiaire choisi
    zone_dest = Frame(page_virement)
    zone_dest.pack(pady=5)
    Label(page_virement, text="Montant ($)").pack()
    champ4 = Entry(page_virement)
    champ4.pack()

    def virement():
        if dest.get() == "":
            erreur_virement("Choisissez un bénéficiaire")
            return
        message = transfert(dest.get(), Numero_compte, champ4.get())
        if message != "Virement effectué":
            erreur_virement(message)
        else:
            jouer_son()
            succes_virement(champ4.get(), dest.get())
        champ4.delete(0, END)
        rafraichir()

    Button(page_virement, text="Envoyer", command=virement).pack(pady=10)

    def afficher(page):
        # montre une seule page à la fois
        page_compte.pack_forget()
        page_virement.pack_forget()
        page.pack(fill=BOTH, expand=True)

    def fermer():
        # ferme l'écran 2 et rouvre l'écran 1
        fenetre1.destroy()
        rouvrir_accueil()

    menu = Menu(fenetre1)
    menu.add_command(label="Mon Compte", command=lambda: afficher(page_compte))
    menu.add_command(label="Virements", command=lambda: afficher(page_virement))
    menu.add_command(label="Fermer la session", command=fermer)

    fenetre1.config(menu=menu)
    fenetre1.protocol("WM_DELETE_WINDOW", fermer)  # la croix fait pareil que Fermer la session
    rafraichir()
    afficher(page_compte)


########### BOUCLE PRINCIPALE #####################################################
console_debut()
accueil()
