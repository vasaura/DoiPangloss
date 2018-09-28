import os, shutil
import xml.etree.ElementTree as ETree
from parsing.DoiGenerator import getLastDoiNumberFromRecord, incrementDoi
from parsing.Parse import parseRecord
from apiDatacite.API_DataCite_Metadata import sendMetadataResource, sendMetadataPhrase
from apiDatacite.API_DataCite_DOI import sendUrlDoiResource, sendUrlDoiPhrase
from constantes import NAMESPACES, PARSE_FILE, DOI_PREFIX, FOLDER_METADATA_RECORD, FOLDER_URL_DOI_RECORD, FOLDER_METADATA_PHRASE, FOLDER_URL_DOI_PHRASE
from parsing.parserAnnotation import parsePhrasesFromAnnotation
from objects.Phrase import Phrase
import sys

if __name__ == "__main__":


    # Récupération du paramétre au lancement du programme
    if len(sys.argv) == 1:
        print("Paramètre manquant. Renseigner add pour traiter uniquemnt les nouvelles ressources ou add_update pour traiter les nouvelles ressources et faire les mises à jour pour le reste")
    else:
        parameter = sys.argv[1]


        # Teste si le paramètre est correctement renseigné
        if parameter != 'add_update' and parameter != 'add':
            print("Paramètre incorrect. Renseigner add ou add_update")

        else:

            # creation et suppression d'un dossier et de son contenu

            shutil.rmtree(FOLDER_METADATA_RECORD)
            shutil.rmtree(FOLDER_URL_DOI_RECORD)
            shutil.rmtree(FOLDER_METADATA_PHRASE)
            shutil.rmtree(FOLDER_URL_DOI_PHRASE)

            os.mkdir(FOLDER_METADATA_RECORD)
            os.mkdir(FOLDER_URL_DOI_RECORD)
            os.mkdir(FOLDER_METADATA_PHRASE)
            os.mkdir(FOLDER_URL_DOI_PHRASE)



            # appel de la fonction getLastDoiNumberFromRecord pour obtenir le dernier numero DOI
            last_doi_number = getLastDoiNumberFromRecord(PARSE_FILE)


            # --------Parse.py OAI-PMH avec etree--------#

            tree = ETree.parse(PARSE_FILE)
            root = tree.getroot()

            # parsing du fichier xml Cocoon
            for index, record in enumerate(root.findall(".//oai:record", NAMESPACES)):

                # appel de la fonction parseRecord pour parser chaque record et créer un objet record
                objetRecord = parseRecord(record)

                # si les droits d'acces à la ressources sont conditionnés par un mot de passe, ne pas créer de DOI
                if 'Access restricted' in objetRecord.droitAccess:
                    continue

                # --------gestion de la reprise après le premier lancement--------#

                # si le doi n'existe pas ou on veut faire une mise à jour pour une ressource existante
                if objetRecord.doiIdentifiant == "" or parameter == "add_update":

                    # si le doi n'existe pas et on veut seulement ajouter les nouveaux identifiants sans mise à jour
                    if objetRecord.doiIdentifiant == "":

                        # appel de la fonction incrementDoi pour créer le nouveau DOI en faisant une incrémentation de 1 à partir du dernier DOI
                        doiNumber, last_doi_number = incrementDoi(last_doi_number)

                        # atttribue à l'objet record créée le numéro doi complet avec le prefixe,
                        # en utilisant une nouvelle affectation à l'attribut identifiant de l'objet.
                        objetRecord.doiIdentifiant = DOI_PREFIX+doiNumber

                    # appel de la methode buildMetadataResource de la classe Record pour générer le fichier xml
                    fichier_xmlRessource = objetRecord.buildMetadataResource()

                    # appel de la méthode generateFileUrlDoiResource pour créer les fichiers avec les url et les DOI
                    fichier_textRessource = objetRecord.generateFileUrlDoiResource()

                    
                    # appel des fonctions pour interroger l'API de Datacite et enregistrer le fichier de metadonnées et le fichier texte avec l'url et le doi pour les ressources
                    if fichier_xmlRessource:
                        sendMetadataResource(fichier_xmlRessource, objetRecord.doiIdentifiant)

                    if fichier_textRessource:
                        sendUrlDoiResource(fichier_textRessource, objetRecord.doiIdentifiant)
                

                    # ---------------------------- PARSING ANNOTATION ---------------------#

                    # extrait le lien url pour chaque fichier xml
                    if objetRecord.lienAnnotation:

                        # appel de la fonction parsePhrasesFromAnnotation pour récupérer une liste avec les id des phrases
                        if parsePhrasesFromAnnotation(objetRecord.lienAnnotation) is not None:
                            listeId, type = parsePhrasesFromAnnotation(objetRecord.lienAnnotation)

                            if listeId:
                                # pour chaque id, génération d'un numéro doi, d'un fichier xml et d'un fichier texte
                                for indexid, id in enumerate(listeId):

                                    # numéro DOI de la phrase
                                    if type == "sentence":
                                        affixe = "S" + str(indexid+1)

                                    elif type == "word":
                                        affixe = "W" + str(indexid+1)
                                    doiPhrase = objetRecord.doiIdentifiant + "." + affixe

                                    # instantiation d'un objet de la classe Phrase
                                    objetPhrase = Phrase(id, doiPhrase, affixe, objetRecord)
                                    # création du fichier xml pour chaque phrase ou mot
                                    fichier_xmlPhrase = objetPhrase.buildMetadataPhrase()
                
                                    # création du fichier texte avec le DOI et l'URL de la phrase
                                    fichier_textPhrase = objetPhrase.generateFileUrlDoiPhrase()
                                    
                                    # methodes pour interroger l'API de Datacite et enregistrer le fichier de metadonnées et le fichier texte
                                    if fichier_xmlPhrase:
                                        sendMetadataPhrase(fichier_xmlPhrase, id)
                
                                    if fichier_textPhrase:
                                        sendUrlDoiPhrase(fichier_textPhrase, doiPhrase, id)
                
                                    # limite le nombre d'itérations pour la phrase et le mot pour tester.
                                    # mettre en commentaire pour faire fonctionner sur la totalité de l'annotation
                                    if indexid == 3:
                                        break

                # limite le nombre d'itérations sur les record et crée un nombre limité de fichiers et de DOI.
                # mettre en commentaire pour faire fonctionner l'application sur la totalité du fichier Cocoon et créer tous les DOI
                if index == 1:
                   break