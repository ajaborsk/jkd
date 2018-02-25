#############
Idées en vrac
#############

Exemples d'applications
=======================

* Analyse immobilisations
* Indicateurs suivi Asset+
* Analyse activité EFS
* Compilation (test)
  Par exemple pour un script Arduino

Structure
=========

Application
-----------

Une application est créée à partir  d'un fichier (xml ?) qui décrit le graphe (noeuds et arcs).


Types de noeuds :
-----------------
 - Source de données (brutes)
     - Base de données
     - Fichier(s) Excel
     - h5
     - fichier brut/binaire (.o .h .c .elf ...)
     - drivers (reflète des données extérieures à l'application)
 - Caches
 - Transformateurs de données (import / export)
 - Table (ou ce serait pluôt un type de données ?)
 - Rapport (pdf/html/dhtml/svg...)
 - noeuds de calcul (Processor)

Noeuds de calcul
----------------

Certains noeuds (notamment de calcul) peuvent comporter du code (python par exemple).
Attention dans ce cas à la sécurité (fake root ? virtualenv ?)
Le code est une donnée (sa mise à jour peut entraîner, en temps réel,la mise à jour de toute l'application)
Prévoir un debugger intégré (avec les fonctions classiques : watch, breakpoints)
Imaginer un debugger de flux = points du code où on envoie dans un
flux des données (valeurs de variables), avec les infos de contexte. Un sorte de
"printf" de debugage mais avec des fonctions évoluées : catégories, caché (pas de code explicite visible), désactivation semi-automatique, etc.
La visualisation/navigation se ferait aussi avec des filtres, de la colorisation, etc.
Prévoir aussi un debugger de flux (du même genre) sur un lien/channel



Tests à prévoir :
 - Tous les Nodes doivent être sérialisables

Serveur http :
--------------

Pour le serveur WEB, typologie des adresses :
  /application/node/subnode/subsubnode#port.[html/xls/pdf/csv/svg]

Rapports :
----------

Un rapport peut être :
  - Offline (contient toutes les données) ou Online (va chercher des données dynamiquement)
  - Static (figé et donc Offline) ou Dynamic (Online or Offline)

Le type est *fixe* : html, pdf, web_page, txt...

Chaque Noeud est identifié de façon unique
MAIS il n'est pas envisageable d'avoir une gestion GLOBALE des identifiants

donc:
 - gestion arborescente (chaque noeud a un ID unique dans son parent)
 - Cela nécessite un système de requête pour rechercher l'id d'un noeud

Communication entre les noeuds
==============================

Chaque Noeud a une entrée sous forme de file d'attente (en:queue) qui reçoit les messages entrants et
une sortie sous forme de liste de triggers qui déclenchent l'envoi de message(s) sur d'autres
noeuds lorsque certaines conditions sont remplies.

Evénements qui peuvent déclencher un trigger :
 - Réception d'un message (suivant le message), avant ou après traitement du message
 - Fin d'exécution d'une tâche interne (bloquante ou non)
 - Etapes intermédiaires d'un (long) calcul


Liens, connexions et messages :
-------------------------------

  Un lien ("link") est un concept de haut niveau (pas d'implémentation)
  qui décrit une relation entre deux ports de deux noeuds.

  Une connexion ("connection") est la concrétisation d'un lien.
  Une connexion est créée par une requête ("query") qui est routée depuis
  le noeud source jusqu'au noeud destination. Elle laisse une trace sur son passage,
  de façon à pouvoir router la ou les réponses de façon simple (pas de calcul de routage)
  et sécurisée (seul l'envoyeur de la requête peut recevoir la ou les réponses).
  Les réponses à une requête peuvent être multiples (abonnement à des mises à jour,
  réponses partielles, informations sur l'avancement du traitement d'une requête complexe...)
  Une connexion peut être fermée par une réponse définitive à une requête (mais ce n'est
  pas impératif)

Liens (links) et politiques (policies) :
----------------------------------------

Chaque port d'entrée d'un noeud "complet" a un lien vers un port de sortie d'un autre noeud.
Ce lien n'est que descriptif.

Les connections / canaux sont créés si nécessaire en utilisant les liens et une "politique" (policy)

Exemples de politiques :
 - A la demande (query/response)
 - Continu dès mise à jour (Subscription)
 - Périodique (autre forme de subscription)

Les politiques peuvent avoir des propriétés :
 - comportement en cas de rupture d'un maillon
    (essai de reconnexion ? pendant combien de temps? etc.)
 - délais/période de mise à jour (indicatif, pour configurer les canaux)
 - nécessité de surveillance (ping/pong sur les canaux)


Messages :
----------

  Les messages sont utilisés pour créer des connexions (requêtes) et transmettre les
  réponses et les éventuelles erreurs. Ils sont constitués d'un dictionnaire (hash), sérialisé ou non suivant
  le mode de transmission.

  Chaque message comporte l'un des trois mots-clefs : 'query', 'reply' ou 'error'.
  Chaque requête comporte un destinataire final, sous forme d'une addresse complète
  (Fully Qualified Name / fqn /path).

  La transmission d'un message entre deux noeuds (qui peuvent être de simples routeurs)
  comporte des tags particuiers :
  *prox_lcid* : proximal query id = identifant local de la requête : créé par l'envoyeur
  pour les requêtes et transmis par l'envoyeur pour les réponses
  *prox_src* : envoyeur (sous un format qui dépend du type de connection)
  *prox_dst* : destinataire (idem).

Trame d'un message :
 - src : id du noeud d'envoi (adresse hiérarchique ?)
 - dst : id du noeud destination (adresse hiérarchique ?)
 - lcid : id de la requête
 - Charge utile :

Routage Aller d'un message :
 - Principe : Toujours passer par le noeud parent, dans la perspective de
            gérer (ultérieurement) les droits d'accès

Routage Retour d'un message :
 - Utiliser les prx_lcid => facile

Création d'un canal :
---------------------

à l'aller (flags = 'c'):
  Noter dans self.channels[lcid] ce qu'il faut faire lors de la réception de la réponse. C'est à dire :
   - le lcid et éventuellement (si queue interne : prx_src, si websocket l'id de ws) la destination (en cas de routage)
   - la coroutine et le client_data pour le noeud qui a lancé la requête (query)
   - Format (NE PAS UTILISER DE {dict} comme valeur car ce n'est pas serialisable) :

    - lors d'une requête (query) :
          self.channels[lcid] = (coroutine_traitement_reponse, client_data)
    - lors d'un routage http (GET or PUT):
          self.channels[lcid] = private_async_queue
    - lors d'un routage ws:
          self.channels[lcid] = (wsid, ws_lcid)
    - lors d'un routage pipe:
          self.channels[lcid] = pipe_lcid
    - lors d'un routage queue:
          self.channels[lcid] = (sender, lcid)

  - Cet enregistrement est fait dans la (co)routine qui appelle msg_send(), ce dernier
     renvoyant lcid si création (None sinon)

au retour (flags = 'f'):
  Noter dans self.back_channels[(incoming lcid, incoming node)] le lcid (déjà créé lors de l'étape 'c')
  Cela permettra de rerouter les messages query_update


Un message a trois drapeaux possibles de propagation (bas niveau). c et f sont exclusifs l'un de l'autre.
'd' peut accompagner n'importe quel message sauf 'c' :

 - 'c' Create => trace son passage - aller - (sauf délégations), pour les Queries
 - 'f' First Use => pour le premier Reply => Crée un channel (retour)
 - ##USELESS 'u' Use => Utilise les traces du channel => utilise un channel
 - 'd' Delete => Supprime les traces après son passage (Query immediate, reply immediate, 'close'...) => Supprime un channel

msg_xxx_deleguate(dest, msg) => envoie un message vers un destinataire (en le forçant) sans laisser de trace (uniquement mode 'c')
msg_xxx_reroute(dest, msg) => envoie un message vers un destinataire sans laisser de trace (uniquement mode 'c')
msg_xxx_transmit(dest, msg) => envoie un message vers un destinataire en gérant la trace (selon les drapeaux du message)
msg_xxx_receive(msg) =>


