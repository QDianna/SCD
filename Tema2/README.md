# Tema 2 - Microservicii & Docker

In aceasta tema am implementat o aplicatie care gestioneaza o baza de date folosind un REST API.

Componente:
1. REST API construit cu Flask
2. Baza de date Mongo
3. Utilitar de gestiune pentru MongoDB - Mongo Express

Configuratie Docker:
- Aplicatia construita utilizeaza docker compose si include urmatoarele servicii:
    1. mongo - container pentru baza de date MongoDB
    2. flask_app - container pentru aplicatia Flask
    3. mongo_express - container pentru aplicatia de gestiune Mongo Express

- Am impartit in 2 retele de Docker:
    1. flask-mongo_network - reteaua in care comunica baza de date cu REST API
    2. express-mongo_network - reteaua in care comunica baza de date cu aplicatia de gestiune

- Am folosit un volum pentru persistenta datelor (din baza de date):
    1. mongo_data - volumul in care sunt stocate colectiile si documentele bazei de date

- Am folosit variabile de mediu pentru a conecta baza de date la aplicatia de gestiune:
    1. ME_CONFIG_MONGODB_SERVER
    2. ME_CONFIG_BASICAUTH_USERNAME
    3. ME_CONFIG_BASICAUTH_PASSWORD

- Porturi folosite:
    1. flask_app: "5000:5000"
    2. mongo: "27017:27017"
    3. mongo-express: "8081:8081"

Fisiere necesare:
.
├── .dockerignore
├── Dockerfile
├── app.py
├── docker-compose.yml
└── requirements.txt

Utilizare:
- Pornire aplicatie:
  > docker-compose up --build
- Accesare interfata mongo-express:
  > http://localhost:8081
- Accesare rute REST API (testate prin intermediul Postman):
  1. POST/api/countries;
  2. GET/api/countries;
  3. PUT/api/countries/:id;
  4. DELETE/api/countries/:id;
  5. POST/api/cities;
  6. GET/api/cities;
  7. GET/api/cities/country/:id_Tara;
  8. PUT/api/cities/:id;
  9. DELETE/api/cities/:id;
  10. POST/api/temperatures;
  11. GET/api/temperatures?lat=Double&lon=Double&from=Date&until=Date;
  12. GET/api/temperatures/cities/:id_oras?from=Date&until=Date;
  13. GET/api/temperatures/countries/:id_tara?from=Date&until=Date;
  14. PUT/api/temperatures/:id;
  15. DELETE/api/temperatures/:id;


