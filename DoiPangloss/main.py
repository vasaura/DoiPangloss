import os, shutil
import sys
PACKAGE_PARENT = '..'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))
import xml.etree.ElementTree as ETree
from parsing.DoiGenerator import getLastDoiNumberFromRecord, incrementDoi, getLastDoiNumberFromDataCite
from parsing.Parse import parseRecord
from apiDatacite.API_DataCite_Metadata import sendMetadataResource, sendMetadataPhrase
from apiDatacite.API_DataCite_DOI import sendUrlDoiResource, sendUrlDoiPhrase
from apiDatacite.API_Get_DataCite_DOI import extractDoiOai
from constantes import NAMESPACES, PARSE_FILE, DOI_PREFIX, FOLDER_METADATA_RECORD, FOLDER_URL_DOI_RECORD, FOLDER_METADATA_PHRASE, FOLDER_URL_DOI_PHRASE
from parsing.parserAnnotation import parsePhrasesFromAnnotation
from objects.Phrase import Phrase


def addDOI():
    
    # appel de la fonction getLastDoiNumberFromRecord pour obtenir le dernier numero DOI
    last_doi_number_cocoon = getLastDoiNumberFromRecord(PARSE_FILE)

    # appel de la fonction getLastDoiNumberFromRecord pour obtenir le dernier numero DOI
    last_doi_number = getLastDoiNumberFromDataCite()

##    if last_doi_number_cocoon != last_doi_number:
##        print ('Certains DOI ne sont pas intégrés dans cocoon')
##    else:
##        print ('DOI à jour dans cocoon')
    
    # parsing du fichier xml Cocoon
    for index, record in enumerate(root.findall(".//oai:record", NAMESPACES)):

        # appel de la fonction parseRecord pour parser chaque record et créer un objet record
        objetRecord = parseRecord(record)

        
        # si les droits d'acces à la ressources sont conditionnés par un mot de passe, ne pas créer de DOI
        if 'Access restricted' in objetRecord.droitAccess:
            continue
        

        # --------gestion de la reprise après le premier lancement--------#
        oaiCocoon = objetRecord.identifiantOAI
        doiCocoon = objetRecord.doiIdentifiant.replace("https://doi.org/","")
        
        dicoDoiOai = {}
        doiExists = True    
        dicoDoiOai = extractDoiOai()
        
        # si la ressource a déjà un doi affecté
        if objetRecord.doiIdentifiant != "":
            doiExists = True

            if doiCocoon in dicoDoiOai and oaiCocoon == dicoDoiOai[doiCocoon]:
                print ('Doi déjà créé pour cette ressource : ', objetRecord.doiIdentifiant)
            # on ne fait rien car le doi existe dans cocoon mais pas dans datacite ! Problème !
            else:
                print ('!!!! Doi déjà créé pour cette ressource mais ne décrit pas la même ressource que dans datacite et dans cocoon (pas le même oai) : ', objetRecord.doiIdentifiant, ' !!!!')
                print ('!!!! MISE A JOUR A FAIRE POUR ECRASEMENT !!!!')
            
        
        # si la ressource n a pas de doi affecté
        else:
            # on vérifie que cet oai n\'a pas un doi dans datacite et que celui ci n\'aurait juste pas encore été intégré dans cocoon
            if (oaiCocoon in dicoDoiOai.values()):
                
                print ('!!!! Doi pas encore créé pour cette ressource mais l\'oai de cette ressource a déjà un doi affecté dans datacite ', oaiCocoon, ' !!!!')
                print ('!!!! CORRIGEZ L\'ERREUR !!!!')
                doiExists = True
                # break
            
            else:
                print ('Doi pas encore créé pour cette ressource : ', oaiCocoon)
                print ('Création et affectation d\'un doi....')
                doiExists = False

        if doiExists == False:
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
            if index == 3:
               break

    
    

def updateDOI():
    
    # appel de la fonction getLastDoiNumberFromRecord pour obtenir le dernier numero DOI
    last_doi_number_cocoon = getLastDoiNumberFromRecord(PARSE_FILE)

    # appel de la fonction getLastDoiNumberFromRecord pour obtenir le dernier numero DOI
    last_doi_number = getLastDoiNumberFromDataCite()

##    if last_doi_number_cocoon != last_doi_number:
##        print ('Certains DOI ne sont pas intégrés dans cocoon')
##    else:
##        print ('DOI à jour dans cocoon')
    
    # parsing du fichier xml Cocoon
    for index, record in enumerate(root.findall(".//oai:record", NAMESPACES)):

        # appel de la fonction parseRecord pour parser chaque record et créer un objet record
        objetRecord = parseRecord(record)

        
        # si les droits d'acces à la ressources sont conditionnés par un mot de passe, ne pas créer de DOI
        if 'Access restricted' in objetRecord.droitAccess:
            continue
        

        # --------gestion de la reprise après le premier lancement--------#
        oaiCocoon = objetRecord.identifiantOAI
        doiCocoon = objetRecord.doiIdentifiant.replace("https://doi.org/","")
       
        
        dicoDoiOai = {}
        doiExists = False    
        dicoDoiOai = extractDoiOai()
        
        # si la ressource à mettre à jour a bien un doi affecté dans cocoon
        if objetRecord.doiIdentifiant != "":
          
            # si la ressource a le meme doi et oai que dans le datacite (si on met bien à jour la meme ressource vs si on ecrase une ressource par une autre)
            if doiCocoon in dicoDoiOai and oaiCocoon == dicoDoiOai[doiCocoon]:  
                print ('Le doi existe bien dans le datacite et correspond bien à la même ressource (meme oai) : ', objetRecord.doiIdentifiant)
                doiExists = True
            else:   
                print ('Le doi existe bien dans le datacite mais correspond a priori une autre ressource (oai différent). Ecrasement.... : ', doiCocoon)
                doiExists = True
            # continue
            
        if doiExists == True:
            print ('Procédure de mise à jour de : ', oaiCocoon, '....' )
            
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
            if index == 3:
               break    
    
    

if __name__ == "__main__":


    # Récupération du paramétre au lancement du programme
    if len(sys.argv) == 1:
        print("Paramètre manquant. Renseigner add pour traiter uniquement les nouvelles ressources ou update pour faire des mises à jour de ressources ayant deja un doi")
    else:
        parameter = sys.argv[1]


        # Teste si le paramètre est correctement renseigné
        if parameter != 'update' and parameter != 'add':
            print("Paramètre manquant. Renseigner add pour traiter uniquement les nouvelles ressources ou update pour faire des mises à jour de ressources ayant deja un doi")

        else:
            # suppression d'un dossier et de son contenu s'il existe
            if os.path.isdir(FOLDER_METADATA_RECORD) and os.path.exists(FOLDER_METADATA_RECORD):
                shutil.rmtree(FOLDER_METADATA_RECORD)
                
            if os.path.isdir(FOLDER_URL_DOI_RECORD) and os.path.exists(FOLDER_URL_DOI_RECORD):
                shutil.rmtree(FOLDER_URL_DOI_RECORD)
            
            if os.path.isdir(FOLDER_METADATA_PHRASE) and os.path.exists(FOLDER_METADATA_PHRASE):
                shutil.rmtree(FOLDER_METADATA_PHRASE)
            
            if os.path.isdir(FOLDER_URL_DOI_PHRASE) and os.path.exists(FOLDER_URL_DOI_PHRASE):
                shutil.rmtree(FOLDER_URL_DOI_PHRASE)
            
            # cree des repertoires s'il n'existent pas
            os.mkdir(FOLDER_METADATA_RECORD)
            os.mkdir(FOLDER_URL_DOI_RECORD)
            os.mkdir(FOLDER_METADATA_PHRASE)
            os.mkdir(FOLDER_URL_DOI_PHRASE)



           


            # --------Parse.py OAI-PMH avec etree--------#

            tree = ETree.parse(PARSE_FILE)
            root = tree.getroot()

            
            if parameter == "add":
                addDOI()
            if parameter == "update":
                updateDOI()
