# Tema 1 - Aplicație Client/Server pentru baze de date folosind RPC

In aceasta tema am implementat un sistem Client-Server folosind protocolul RPC si arhitectura OAuth.
Sistemul consta in interactiuni intre client si server pentru autentificare, gestionare acces si executare
de actiuni pe anumite resurse.


Componente:
1. Client (`rpc_client_config.c`):
  - este partea responsabila cu initierea interactiunilor, procesand cereri de la useri (`client.in`) si trimitand
  cereri catre server
  - mentine o structura de date locala (`Users`) pentru a tine evidenta utilizatorilor si a tokenurilor de acces
  asociate acestora

2. Server (`rpc_server_config.c`):
  - se ocupa atat de autorizare cat si de gestionarea resurselor
  - simuleaza interactiunea cu end-userul prin citirea "raspunsurilor" acestuia dintr un fisier (`approvals.db`)
  si procesarea acestora


Structuri si metode ale interfetei RPC:
1. Structuri de date
  - `AuthZRequest`: structura reprezinta cererea de autorizare initiata de client; este necesara 
  pentru a solicita serverului sa valideze un utilizator si sa genereze un authz token.
  - `AuthZResponse`: structura reprezinta raspunsul serverului la o cerere de autorizare; este necesara 
  pentru a transmite clientului rezultatul validarii si, in caz de succes, tokenul de autorizare generat.
  - `AccessTokenRequest`: este structura utilizata de client pentru a solicita un token de access 
  pe baza unui token de autorizare.
  - `AccessTokenResponse`: structura utilizata de server pentru a transmite clientului raspunsul la cererea de acces; 
  intoarce rezultatul validarii si, in caz de succes, tokenul de access; daca requestul a avut auto_refresh = 1 
  va intoarce si un refresh token pentru client.
  - `DelegatedAction`: structura reprezinta o actiune pe o resursa a serverului pe care clientul vrea sa o execute.
  - `DelegatedActionResponse`: structura reprezinta raspunsul serverului la cererile de acțiuni delegate; intoarce un
  mesaj cu rezultatul actiunii

2. Metode
- `requestAuthZ`: primește o cerere de autorizare si returnează un raspuns care contine, in caz de succes,
un token de autorizare.
- `approveAuthZ`: simuleaza end-userul; primeste raspunsul la cererea de autorizare anterioara si procesează 
aprobarea utilizatorului final, asociind, la nivel de server, permisiunile cu tokenul de autorizare.
- `generateAccessToken`: primeste o cerere de acces si returneaza un raspuns care contine, in caz de succes, 
un token de acces generat pe baza unui token de autorizare valid.
- `refreshAccessToken`: primeste o cerere de refresh si returneaza un raspuns care contine, in caz de succes, 
un token de acces generat pe baza unui token de refresh valid.
- `executeDelegatedAction`: primeste o actiune delegata si verifica daca userul are permisiunile necesare, 
intorcand un raspuns care contine un mesaj cu rezultatul actiunii


Workflow:
1. Initializare
- Clientul:
  - creeaza o conexiune catre server folosind `clnt_create`
  - citeste comenzile din fisierul `client.in` si le proceseaza una cate una
- Serverul:
  - se initializeaza incarcand datele din fisierele `userIDs.db`, `approvals.db` si `resources.db`
  - configureaza ttl-ul (time to live) pentru token-uri

2. Comanda REQUEST
  2.1: Solicitare de autorizare
  - Clientul:
    - trimite o cerere de autorizare (`requestAuthZ`) catre server, specificand `user_id`
  - Serverul:
    - verifica daca utilizatorul exista in `userIDs_db`
    - daca utilizatorul este valid, genereaza un authz token si returneaza un `AuthZResponse` cu acest token

  2.2: Aprobare autorizare (simulare end-user)
  - Clientul:
    - primeste token-ul de autorizare din raspunsul serverului si initiaza aprobarea prin apelarea 
    functiei `approveAuthZ`
  - Serverul:
    - simuleaza comportamentul end-user-ului citind raspunsuri din `approvals.db`
    - pe baza raspunsului, stabileste permisiunile asociate token-ului de autorizre si actualizeaza 
    structura interna `valid_tokens`; trimite un raspuns care confirma starea aprobarii

  2.3: Solicitare de acces
  - Clientul:
    - foloseste token-ul de autorizare aprobat pentru a solicita un token de acces prin apelarea 
    functiei `generateAccessToken`.
    - daca este setat flag-ul auto_refresh, include aceasta optiune in cerere.
    - actualizeaza structura locala `Users` cu noile token-uri primite si stocheaza informatiile despre TTL.
  - Serverul:
    - valideaza authz token si genereaza un token de acces.
    - daca auto_refresh este activ, genereaza si un token de refresh.
    - returneaza token-urile de acces si, optional, cel de refresh.

3. Comenzile RIMDX (READ, INSERT, MODIFY, DELETE, EXECUTE)
  3.1: Verificarea token-ului
  - Clientul:
    - verifica daca utilizatorul exista in structura locala `Users`
    - daca token-ul de acces a expirat si auto_refresh este activ, trimite o cerere de refresh 
    (`refreshAccessToken`) catre server
  - Serverul:
    - valideaza token-ul de refresh si genereaza un token-uri noi de acces si refresh
    - actualizeaza structura interna `valid_tokens` si returneaza noile token-uri

  3.2: Actiunea delegata
  - Clientul:
    - trimite o cerere de actiune delegata (`executeDelegatedAction`) catre server, specificand operatia si resursa
  - Serverul:
    - valideaza token-ul de acces inclus in cererea clientului
    - verifica daca utilizatorul are permisiunea de a realiza operatiunea dorita asupra resursei specificate
    - daca permisiunea este acordata:
      - executa actiunea delegata
      - returneaza un raspuns care confirma succesul operatiunii
    - daca permisiunea este refuzata, returneaza un mesaj de eroare cu un cod corespunzator

  
