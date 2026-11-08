import tkinter as tk

import sqlite3

import random

import msvcrt

def saisir_cache(question):
    print(question, end="", flush=True)
    texte = ""
    while True:
        touche = msvcrt.getwch()
        if touche in ("\r", "\n"):      # ENTRÉE
            print()
            return texte
        elif touche == "\b":             # RETOUR ARRIÈRE
            if len(texte) > 0:
                texte = texte[:-1]
                print("\b \b", end="", flush=True)
        else:
            texte += touche
            print("*", end="", flush=True)


connexion = sqlite3.connect("banque.db")
cursor = connexion.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS comptes (account_number INTEGER, balance INTEGER, password TEXT, secret_phrase TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS numeros_restants (numero INTEGER)")

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

        password = saisir_cache("Choisissez votre mot de passe et pressez sur ENTRÉE : ")
        password_conf = saisir_cache("Confirmez votre mot de passe puis pressez sur ENTRÉE : ")
        while password_conf != password:
            password_conf = saisir_cache("Les mots de passe ne correspondent pas, réessayez : ")

        voir = input("Tapez 1 pour voir le mot de passe, ou ENTRÉE pour continuer : ")
        if voir == "1":
            print("Votre mot de passe :", password)

        # Base de données
        cursor.execute("DELETE FROM numeros_restants WHERE numero = ?", (num_compte,))
        cursor.execute("INSERT INTO comptes VALUES (?, ?, ?, ?)", (num_compte, argent, password, phrase_mot))
        connexion.commit()

connexion.close()

def acceuil():
    global fenetre
    fenetre = Tk()
    fenetre.geometry("400x600")
    Label(fenetre, text="Banque Grasséenne").pack(pady=20)
    Label(fenetre, text="Type de connexion").pack()
    Label(fenetre, text="*Client *Admin").pack(pady=20)
    Label(fenetre, text="Numéro de compte").pack()
    champ= Entry(fenetre)
    champ.pack(pady=20)
    champ.bind("<Return>",motdepass)
    def motdepass(event):
        Label(fenetre, text="Mots de passes").pack()
        champ2=Entry(fenetre)
        champ2.pack(pady=20)
    Bouton1=Button(fenetre, text="Ouvrir la session", command=session)
    Bouton1.pack(pady=20)
    Bouton2=Button(fenetre, text="Mots de passes oublié ?", command=Motsdepasses_oublié)

    fenetre.mainloop()

def session():
    fenetre.destroy()
    pass
def Motsdepasses():
    pass

