# Spécifications techniques de l'application DoiPangloss

L'application DoiPangloss est une application développée en Python qui prend en entrée un fichier XML du modèle Cocoon et génère pour chaque ressource et chaque phrase ou mot constituant les fichiers d'annotations, des fichiers XML, des fichiers texte (contenant les noms DOI et les liens URL) et les enregistre auprès de Datacite. Elle produit actuellement des DOI de tests, donc elle peut être lancée en toute sécurité. 

## Structuration des fichiers et des dossiers
L'application contient à la racine les éléments suivants:
* 4 dossiers qui représentent des packages Python: *apiDatacite*, *data*, *objects* et *parsing*
* 2 fichiers python `main.py` et `constantes.py` et un fichier `critical.log`
* un fichier `__init__.py` est présent dans chaque dossier (sauf dans *data*) et a pour rôle d'indiquer le fait que le dossier est un package python. 

### Le dossier *data* contient 
* 4 dossiers : *testPhrase*, *testRecord*, *testURL_Phrase*, *testURL_Record*. Ils ont le rôle de stocker les fichiers XML du modèle DOI et les fichiers textes générés au lancement de l'application. 
* le fichier `metadata_cocoon.xml` qui représente le fichier XML contenant les métadonnées des ressources de la collection Pangloss. C'est le fichier qui est utilisé en entrée par l'application pour générer les DOI et les enregistrer auprès de DataCite
* le fichier `lacito_verif.xml` est un fichier de test qui permet de faire des tests individuels pour une seule ressource. Il est indépendant du reste de l'application, mais très utile pour les tests. 
* le fichier `sortie.xml` est un fichier de test, le résulat du traitement individuel du fichier `lacito_verif.xml`. Il est indépendant du reste de l'application
* les fichers `apiMetadonnees` et `apiUrl`qui ont le rôle d'enregistrer les réponses envoyées par le serveur de DataCite aux requêtes PUT et POST.

### Le package *apiDatacite* contient les modules pour interroger l'API de DataCite:
* le module *API_DataCite_DOI* envoie à DataCite le lien URL et le nom DOI de la ressource et de la phrase
* le module *API_DataCite_Metadata* envoie à DataCite le fichier de métadonnées de la ressource et de la phrase
* le module *API_Get_DataCite_DOI* récupère de DataCite les fichiers de métadonnées des DOI de la Collection Pangloss. Ce module n'est pas encore utilisé. Il sera fonctionnel après la mise en production. (il ne fonctionne que pour des DOI réels et non pas pour des DOI de tests)

### Le package *objects* contient les deux classes *Record* et *Phrase*. 
Les deux classes contiennent des méthodes qui assurent la génération des fichiers XML selon le modèle DOI et des fichiers texte contenant les liens URL et les noms DOI. 

### Le package *parsing* contient les modules qui assurent différentes phases du parsing des fichiers textuels. 
* le module *DoiGenerator* est destiné à récupérer le dernier numéro DOI et à créer un nouveau DOI incrémenté de 1. 
* le module *Parse* a pour rôle de parser un record du fichier `metadata_cocoon.xml` et de récupérer les valeurs des balises qui composent un record 
* le module *parserAnnotation* a pour rôle de parser un fichier XML d'annotation qui est récupéré par une requête HTTP et de fournir une liste avec les id xml de chaque phrase ou mot de l'annotation.
* le module *parserOneRecord* est un module de test qui permet de réaliser le parsing du fichier `lacito_verif.xml` (représentant un seul record) et la génération du fichier selon le modèle DOI, `sortie.xml`. Ce module est indépendant du reste de l'application. 
 

## Execution de l'application.

### Prérequis:
* Installer Python 3.6.
* installer la librairie *requests* de python avec la commande suivante `pip install requests` 

### Execution
Pour lancer l'application, executez le fichier `main.py` auquel il faut rajouter un paramètre: *add* ou *add_update*.
Dans le terminal, déplacez-vous à la racine du dossier DoiPangloss et lancez le fichier `main.py` en tapant :  
`python3 main.py add` pour créer des noms DOI pour les nouvelles ressources
ou 
`python3 main.py add_update` pour créer des noms DOI pour les nouvelles ressources et pour mettre à jour les anciens DOI. 

Pour lancer l'application avec l'interpréteur pycharm, configurez d'abord les paramètres d'exécution du fichier main. Dans la barre de tâches de pycharm allez dans le menu Run et cliquez sur Edit Configuration. 
Dans le champ 'script Path', vérifiez que le fichier à exécuter est `main.py`.
Dans le champ 'Parameters', ajoutez `add` ou `add_update`

Pour enregistrer des DOI sur le site de DataCite, il faut avoir un nom d'utilisateur et un mot de passe. 
Insérer dans le fichier `constantes.py`les informations suivantes (lignes 21, 22):
* USERNAME
* PASSWORD  

Pour executer l'application sans faire les requêtes vers DataCite, mettre en commentaires les lignes 69-74 et les lignes 106-111.

L'application est fournie avec le fichier de métadonnées à parser (`metadata_cocoon.xml`). Si vous désirez parser un nouveau fichier Cocoon, il faut s'assurer que le fichier xml à parser se trouve dans le dossier *data*. Si le nom du fichier est différent du fichier actuel (`metadata_cocoon.xml`) il faut le changer dans `constantes.py` (la variable PARSE_FILE ligne 1)

Actuellement l'application crée des DOI pour les 15 premières ressources et pour les 3 premières phrases. Pour créer des DOI pour la totalité des ressources et des phrases (environ 170 000 DOI), mettez en commentaire les lignes 115, 116, 120, 121 du fichier `main.py`. 

### Tester un seul record:
* le fichier xml sur lequel fonctionne le test est `lacito_verif.xml` 
* ouvrir le `lacito_1verif.xml` remplacer le contenu de la balise <record> avec un nouveau record à tester. 
* Rajouter l'espace de nom avec le préfixe (xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" affiché dans les commentaires : ligne 2) dans la balise <olac:olac> au côté des autres espaces de nom. 
	*Par exemple <olac:olac xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:olac="http://www.language-archives.org/OLAC/1.1/" xsi:schemaLocation="http://www.language-archives.org/OLAC/1.1/ http://www.language-archives.org/OLAC/1.1/olac.xsd">
* lancer le fichier `parserOneRecord.py`
* vérifier le résultat: le fichier `sortie.xml`
