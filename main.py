from tkinter import *


import sqlite3

import random

################ connexion base de donner #########

connexion = sqlite3.connect("banque.db")
cursor = connexion.cursor()


############## CREER SI PAS EXISTANT #########################33
cursor.execute("CREATE TABLE IF NOT EXISTS comptes (num_compte INTEGER, argent INTEGER, password TEXT, phrase_mot TEXT)")
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
admin_compte = False
password_adm = "123"
nom_adm = "adm"


############################ FONCTION RECOLTE BASE DE DONNER ET MODIFIER ####################



    ## FONCTION RECOLTE MOTS DE PASSE CELON LE NOM DE L'utilisateur

##### verificatio
def verification_mdp_client(numero_compte, mots_depasses):
    conn = sqlite3.connect("banque.db")
    curs = conn.cursor()

    curs.execute("SELECT password FROM comptes WHERE num_compte = ?", (int(numero_compte),))
    resultat = curs.fetchone()   # (mot_de_passe,) ou None si le compte n'existe pas
    conn.close()

    if resultat is None:
        return False             # compte inexistant
    return resultat[0] == mots_depasses

def verification_mdp_admin(numero_compte, mots_depasses):


    return numero_compte == nom_adm and password_adm == mots_depasses


############################# CLIENT ############################
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

def session_Admin():
    fenetre2 = Tk()

def session_client():
    fenetre.destroy()
    fenetre1 = Tk()
    pass
def accueil():
    global fenetre, champ, Admin, champ2
    fenetre = Tk()
    fenetre.geometry("400x600")
    Label(fenetre, text="Banque Grasséenne").pack(pady=20)
    Label(fenetre, text="Type de connexion").pack()
    Admin = StringVar()  # variable Tkinter, pas un booléen
    Admin.set("client")

    Radiobutton(fenetre, text="Admin", variable=Admin, value="admin").pack(anchor=CENTER)
    Radiobutton(fenetre, text="Client", variable=Admin, value="client").pack(anchor=CENTER)

    Label(fenetre, text="Numéro de compte").pack(pady=10)
    champ = Entry(fenetre)
    champ.pack(pady=10)
    champ2=None
    def motdepass(event):
        global champ2
        Label(fenetre, text="Mots de passes").place(relx=0.5, rely=0.4, anchor=CENTER)
        champ2=Entry(fenetre)
        champ2.place(relx=0.5, rely=0.45, anchor=CENTER)
    champ.bind("<Return>",motdepass)
    def connexion():
        if champ2==None:
            motdepass(None)
        elif Admin.get()=="admin":
            if verification_mdp_admin(champ.get(), champ2.get()):
                session_Admin()
            else:
                erreur_connexion()
        elif Admin.get()=="client":
            if verification_mdp_client(champ.get(), champ2.get()):
                session_client()
            else:
                erreur_connexion()
    Bouton1 = Button(fenetre, text="Ouvrir la session", command=connexion)
    Bouton1.place(relx=0.5, rely=0.6, anchor=CENTER)
    Bouton2 = Button(fenetre, text="Mots de passes oublié ?", command=Motsdepasses_oublié)
    Bouton2.place(relx=0.5, rely=0.67, anchor=CENTER)
    fenetre.mainloop()


def Motsdepasses_oublié():
    numero = champ.get().strip()

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
        curs.execute("SELECT password FROM comptes WHERE account_number = ?", (int(numero),))
        resultat = curs.fetchone()                 # (mot_de_passe,) ou None
        conn.close()

        if resultat is None:
            print("Vous n'avez pas de compte client")
        else:
            print(resultat[0])







########### BOUCLE PRINCIPALES #####################################################
console_debut()
accueil()
