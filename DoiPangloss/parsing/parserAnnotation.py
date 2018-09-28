# --------Parsing XML ------------------#
import xml.etree.ElementTree as ET
import requests
import logging
from constantes import CRITICAL_LOG

logging.basicConfig(filename=CRITICAL_LOG,level=logging.INFO)


def parsePhrasesFromAnnotation (lienUrl):
    """
    Fonction qui récupère le lien url du fichier d'annotations, parse le fichier et retroune la liste des identifiants XMl
    Elle retourne None si le lien ne fonctionne pas
    :param lienUrl: lien URL du fichier d'annotations en XML
    :return: la liste des identifiants XML, le type de structure (word ou sentence)
    :rtype: list, str
    """
    type = ""
    # fait une requête de type GET sur Huma-Num, le lieu d'hébérgement du lien des annotations
    req = requests.get(lienUrl)

    # si la réponse est différente de 200 et 201
    if req.status_code !=200 and req.status_code != 201:
        # envoie un message d'erreur
        message = "Le lien {} ne fonctionne pas".format(lienUrl)
        logging.error(message)
        print(message)

        return None

    else:
        root = ET.fromstring(req.text)
        listeID = []
        # vérifie que la balise <S> existe
        if root.findall('.//S'):
            type="sentence"
            # itère sur chaque élément <S>
            for phrase in root.findall('.//S'):
                # parse les attributs de la balise <S>
                attributsPhrase = phrase.attrib
                # extrait la valeur de l'attribut "id"
                idPhrase = attributsPhrase.get("id")
                listeID.append(idPhrase)
        # si la balise <S> n'existe pas, parse la balise <W>
        elif root.findall('.//W'):
            type = "word"
            for mot in root.findall('.//W'):
                # parse les attributs de la balise <W>
                attributsMot = mot.attrib
                # extrait la valeur de l'attribut "id"
                idMot = attributsMot.get("id")
                listeID.append(idMot)

        # si le fichier ne contient aucune des deux balises, affiche un message d'erreur
        else:
            message = "Le fichier {} d'annotation n'est pas structuré".format(lienUrl)
            logging.error(message)

        return listeID, type