from flask import Flask, Response, request
from flask_pymongo import PyMongo
from datetime import datetime
import json
import time

# init flask app
app = Flask(__name__)

# init mongo db
app.config["MONGO_URI"] = "mongodb://mongo:27017/tema2scd"
mongo = PyMongo(app)

# config indexes on mongo db
def configure_mongodb():
    try:
        mongo.db.countries.create_index("nume_tara", unique=True)
        mongo.db.cities.create_index([("id_tara", 1), ("nume_oras", 1)], unique=True)
        mongo.db.temperatures.create_index([("id_oras", 1), ("timestamp", 1)], unique=True)
    except Exception as e:
        print(e)


# route 1: add a country to db
@app.route('/api/countries', methods = ['POST'])
def post_country():
    try:
        data = request.get_json()
        if not data:
            return Response(
                json.dumps({"error" : "invalid data, please include all required fields"}),
                status = 400,
                mimetype = 'application/json'
            )
        
        # verify the existence of all required fields for POST request
        required_fields = ["nume", "lat", "lon"]
        for field in required_fields:
            if field not in data:
                return Response(
                    json.dumps({"error" : "invalid data, please include all required fields"}),
                    status = 400,
                    mimetype = 'application/json'
                )

        # check if the required fields have the correct type
        if (
            not isinstance(data.get("nume"), str) or 
            not isinstance(data.get("lat"), (float, int)) or 
            not isinstance(data.get("lon"), (float, int))
        ):
            return Response(
                json.dumps({"error" : "invalid data, please use correct data type for required fields"}),
                status = 400,
                mimetype = 'application/json'
            )
        
        # get the next available index for this entry
        max_id = mongo.db.countries.find_one(sort = [("id", -1)])
        new_id = (max_id["id"] + 1) if max_id else 1

    
        country = {
            "id" : new_id,
            "nume_tara" : data["nume"],
            "latitudine" : data["lat"],
            "longitudine" : data["lon"]
        }

        mongo.db.countries.insert_one(country)

        return Response(
            json.dumps({"id": new_id}),
            status = 201,
            mimetype = 'application/json'
        )
    
    except Exception as e:
        if "duplicate key error" in str(e).lower():
            return Response(
                json.dumps({"error" : "a country with this name already exists"}),
                status = 409,
                mimetype = 'application/json'
            )
        
        return Response(
            json.dumps({"error" : str(e)}),
            status = 500,
            mimetype = 'application/json'
        )

# route 2: get all countries
@app.route('/api/countries', methods = ['GET'])
def get_countries():
    try:
        countries = list(mongo.db.countries.find())

        result = [
            {
                "id": c["id"],
                "nume": c["nume_tara"],
                "lat": c["latitudine"],
                "lon": c["longitudine"]
            }
            for c in countries
        ]

        return Response(
            json.dumps(result, sort_keys=False),
            status = 200,
            mimetype = 'application/json'
        )
    
    except Exception as e:
        return Response(
            json.dumps({"error" : str(e)}),
            status = 500,
            mimetype = 'application/json'
        )

# route 3: modify a country
@app.route('/api/countries/<int:id>', methods = ['PUT'])
def put_country(id):
    try:
        data = request.get_json()
        if not data:
            return Response(
                json.dumps({"error" : "invalid data, please include all required fields"}),
                status = 400,
                mimetype = 'application/json'
            )
        
        # verify the existence of all required fields for PUT request
        required_fields = ["id", "nume", "lat", "lon"]
        if not all (field in data for field in required_fields):
            return Response(
                json.dumps({"error" : "invalid data, please include all required fields"}),
                status = 400,
                mimetype = 'application/json'
            )
        
        # check if the required fields have the correct type
        if (
            not isinstance(data.get("id"), int) or 
            not isinstance(data.get("nume"), str) or 
            not isinstance(data.get("lat"), (float, int)) or 
            not isinstance(data.get("lon"), (float, int))
        ):
            return Response(
                json.dumps({"error" : "invalid data, please use correct data type for required fields"}),
                status = 400,
                mimetype = 'application/json'
            )
        
        # check if the id is valid for the route used
        if data.get("id") != id:
            return Response(
                json.dumps({"error" : "invalid data, please use the same id as in route"}),
                status = 400,
                mimetype = 'application/json'
            )
        
        result = mongo.db.countries.update_one(
            {"id" : id},
            {"$set" : {
                "nume_tara" : data.get("nume"),
                "latitudine" : data.get("lat"),
                "longitudine" : data.get("lon")
            }}
        )

        if result.matched_count == 0:
            return Response(
                json.dumps({"error" : "country was not found"}),
                status = 404,
                mimetype = 'application/json'
            )
    
        return Response(status = 200)
    
    except Exception as e:
        if "duplicate key error" in str(e).lower():
            return Response(
                json.dumps({"error" : "a country with this name already exists"}),
                status = 409,
                mimetype = 'application/json'
            )
        
        return Response(
            json.dumps({"error" : str(e)}),
            status = 500,
            mimetype = 'application/json'
        )

# route 4: delete a country
@app.route('/api/countries/<int:id>', methods = ['DELETE'])
def delete_country(id):
    try:
        result = mongo.db.countries.delete_one(
            {"id" : id}
        )

        if result.deleted_count == 0:
            return Response(
                json.dumps({"error" : "country was not found"}),
                status = 404,
                mimetype = 'application/json'
            )
    
        return Response(status = 200)
    
    except Exception as e:
        return Response(
            json.dumps({"error" : str(e)}),
            status = 500,
            mimetype = 'application/json'
        )


# route 5: add a city to db
@app.route('/api/cities', methods = ['POST'])
def post_city():
    try:
        data = request.get_json()
        if not data:
            return Response(
                json.dumps({"error" : "invalid data, please include all required fields"}),
                status = 400,
                mimetype = 'application/json'
            )
        
         # verify the existence of all required fields for POST request
        required_fields = ["idTara", "nume", "lat", "lon"]
        if not all(field in data for field in required_fields):
            return Response(
                json.dumps({"error" : "invalid data, please include all required fields"}),
                status = 400,
                mimetype = 'application/json'
            )
        
        # check if the required fields have the correct type
        if (
            not isinstance(data.get("idTara"), int) or 
            not isinstance(data.get("nume"), str) or 
            not isinstance(data.get("lat"), (float, int)) or 
            not isinstance(data.get("lon"), (float, int))
        ):
            return Response(
                json.dumps({"error" : "invalid data, please use correct data type for required fields"}),
                status = 400,
                mimetype = 'application/json'
            )
        
        # check if the country id is valid
        country_exists = mongo.db.countries.find_one({"id": data["idTara"]})
        if not country_exists:
            return Response(
                json.dumps({"error" : "city's country was not found"}),
                status = 404,
                mimetype = 'application/json'
            )

        # get the next available index for this entry
        max_id = mongo.db.cities.find_one(sort = [("id", -1)])
        new_id = (max_id["id"] + 1) if max_id else 1

        city = {
            "id" : new_id,
            "id_tara" : data.get("idTara"),
            "nume_oras" : data.get("nume"),
            "latitudine" : data.get("lat"),
            "longitudine" : data.get("lon")
        }

        mongo.db.cities.insert_one(city)

        return Response(
            json.dumps({"id" : new_id}),
            status = 201,
            mimetype = 'application/json'
        )
    
    except Exception as e:
        if "duplicate key error" in str(e).lower():
            return Response(
                json.dumps({"error" : "a city with this name already exists"}),
                status = 409,
                mimetype = 'application/json'
            )
        
        return Response(
            json.dumps({"error" : str(e)}),
            status = 500,
            mimetype = 'application/json'
        )

# route 6: get all cities
@app.route('/api/cities', methods = ['GET'])
def get_cities():
    try:
        cities = list(mongo.db.cities.find())
        result = [
            {
                "id" : c["id"],
                "idTara" : c["id_tara"],
                "nume" : c["nume_oras"],
                "lat" : c["latitudine"],
                "lon" : c["longitudine"]
            }
            for c in cities
        ]

        return Response(
            json.dumps(result, sort_keys = False),
            status = 200,
            mimetype = 'application/json'
        )
    
    except Exception as e:
        return Response(
            json.dumps({"error" : str(e)}),
            status = 500,
            mimetype = 'application/json'
        )

# route 7: get cities of a coutry
@app.route('/api/cities/country/<int:id>', methods = ['GET'])
def get_country_cities(id):
    try:
        cities = list(mongo.db.cities.find(
            {"id_tara" : id}
        ))

        result = [
            {
                "id" : c["id"],
                "idTara" : c["id_tara"],
                "nume" : c["nume_oras"],
                "lat" : c["latitudine"],
                "lon" : c["longitudine"]
            }
            for c in cities
        ]

        return Response(
            json.dumps(result, sort_keys=False),
            status=200,
            mimetype='application/json'
        )
    
    except Exception as e:
        return Response(
            json.dumps({"error" : str(e)}),
            status = 500,
            mimetype = 'application/json'
        )

# route 8: modify a city
@app.route('/api/cities/<int:id>', methods = ['PUT'])
def put_city(id):
    try:
        data = request.get_json()
        if not data:
            return Response(
                json.dumps({"error" : "invalid data, please include all required fields"}),
                status = 400,
                mimetype = 'application/json'
            )
        
        # verify the existence of all required fields for PUT request
        required_fields = ["id", "idTara", "nume", "lat", "lon"]
        if not all (field in data for field in required_fields):
            return Response(
                json.dumps({"error" : "invalid data, please include all required fields"}),
                status = 400,
                mimetype = 'application/json'
            )
                
        # check if the required fields have the correct type
        if (
            not isinstance(data.get("id"), int) or 
            not isinstance(data.get("idTara"), int) or 
            not isinstance(data.get("nume"), str) or 
            not isinstance(data.get("lat"), (float, int)) or 
            not isinstance(data.get("lon"), (float, int))
        ):
            return Response(
                json.dumps({"error" : "invalid data, please use correct data type for required fields"}),
                status = 400,
                mimetype = 'application/json'
            )
        
        # check if the request's id is valid for the route used
        if data.get("id") != id:
            return Response(
                json.dumps({"error" : "invalid data, please use the same id as in route"}),
                status = 400,
                mimetype = 'application/json'
            )
        
        # check if the country id is valid
        country_exists = mongo.db.countries.find_one({"id": data["idTara"]})
        if not country_exists:
            return Response(
                json.dumps({"error" : "city's country was not found"}),
                status = 404,
                mimetype = 'application/json'
            )
        
        result = mongo.db.cities.update_one(
            {"id" : id},
            {"$set" : {
                "id_tara" : data.get("idTara"),
                "nume_oras" : data.get("nume"),
                "latitudine" : data.get("lat"),
                "longitudine" : data.get("lon")
            }}
        )

        if result.matched_count == 0:
            return Response(
                json.dumps({"error" : "city was not found"}),
                status = 404,
                mimetype = 'application/json'
            )
    
        return Response(status = 200)
    
    except Exception as e:
        if "duplicate key error" in str(e).lower():
            return Response(
                json.dumps({"error" : "a city with this name already exists"}),
                status = 409,
                mimetype = 'application/json'
            )
        
        return Response(
            json.dumps({"error" : str(e)}),
            status = 500,
            mimetype = 'application/json'
        )

# route 9: delete a city
@app.route('/api/cities/<int:id>', methods = ['DELETE'])
def delete_city(id):
    try:
        result = mongo.db.cities.delete_one(
            {"id" : id}
        )

        if result.deleted_count == 0:
            return Response(
                json.dumps({"error" : "city was not found"}),
                status = 404,
                mimetype = 'application/json'
            )
    
        return Response(status = 200)
    
    except Exception as e:
        return Response(
            json.dumps({"error" : str(e)}),
            status = 500,
            mimetype = 'application/json'
        )


# route 10: add a temperature mesurement to db
@app.route('/api/temperatures', methods = ['POST'])
def post_temperature():
    try:
        data = request.get_json()
        if not data:
            return Response(
                json.dumps({"error" : "invalid data, please include all required fields"}),
                status = 400,
                mimetype = 'application/json'
            )
        
        # verify the existence of all required fields for POST request
        required_fields = ["idOras", "valoare"]
        if not all (field in data for field in required_fields):
            return Response(
                json.dumps({"error" : "invalid data, please include all required fields"}),
                status = 400,
                mimetype = 'application/json'
            )
        
        # check if the required fields have the correct type
        if (
            not isinstance(data.get("idOras"), int) or 
            not isinstance(data.get("valoare"), (float, int))
        ):
            return Response(
                json.dumps({"error" : "invalid data, please use correct data type for required fields"}),
                status = 400,
                mimetype = 'application/json'
            )
        
        # check if the city id is valid
        city_exists = mongo.db.cities.find_one({"id": data["idOras"]})
        if not city_exists:
            return Response(
                json.dumps({"error" : "city was not found"}),
                status = 404,
                mimetype = 'application/json'
            )
        
        # get the next available index for this entry
        max_id = mongo.db.temperatures.find_one(sort = [("id", -1)])
        new_id = (max_id["id"] + 1) if max_id else 1

        # create a timestamp for the entry
        timestamp = datetime.now()
    
        temperature = {
            "id" : new_id,
            "valoare" : data.get("valoare"),
            "timestamp" : timestamp,
            "id_oras" : data.get("idOras"),
        }
        mongo.db.temperatures.insert_one(temperature)

        return Response(
            json.dumps({"id" : new_id}),
            status = 201,
            mimetype = 'application/json'
        )
    
    except Exception as e:
        if "duplicate key error" in str(e).lower():
            return Response(
                json.dumps({"error" : "there's already a temperature entry for this city and time"}),
                status = 409,
                mimetype = 'application/json'
            )
        return Response(
            json.dumps({"error" : str(e)}),
            status = 500,
            mimetype = 'application/json'
        )

# route 11: get temperatures based on lat, lon, start date and/or end date
@app.route('/api/temperatures', methods = ['GET'])
def get_temperatures_filtered():
    try:
        # extract filter information (if any) from arguments
        lat = request.args.get("lat", type = float)
        lon = request.args.get("lon", type = float)
        start_date = request.args.get("from")
        end_date = request.args.get("until")

        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")

        # create a query with filter information
        query = {}

        # add location filter - latitude and/or longitude of the city - to query
        if lat is not None and lon is not None:
            cities = mongo.db.cities.find({"latitudine" : lat, "longitudine" : lon})
            cities_ids = [c["id"] for c in cities]
            query["id_oras"] = {"$in" : cities_ids}
        elif lat is not None:
            cities = mongo.db.cities.find({"latitudine" : lat})
            cities_ids = [c["id"] for c in cities]
            query["id_oras"] = {"$in" : cities_ids}
        elif lon is not None:
            cities = mongo.db.cities.find({"longitudine" : lon})
            cities_ids = [c["id"] for c in cities]
            query["id_oras"] = {"$in" : cities_ids}

        # add timestamp filter - start and/or end date(s) - to query
        if start_date and end_date:
            query["timestamp"] = {"$gte" : start_date, "$lte" : end_date}
        elif start_date:
            query["timestamp"] = {"$gte" : start_date}
        elif end_date:
            query["timestamp"] = {"$lte" : end_date}

        # apply the query on the temperatures collection
        temperatures = list(mongo.db.temperatures.find(query))

        result = [
            {
                "id" : t["id"],
                "valoare" : t["valoare"],
                "timestamp" : t["timestamp"].strftime("%Y-%m-%d")
            }
            for t in temperatures
        ]

        return Response(
            json.dumps(result, sort_keys = False),
            status = 200,
            mimetype = 'application/json'
        )
    
    except Exception as e:

        return Response(
            json.dumps({"error" : str(e)}),
            status = 500,
            mimetype = 'application/json'
        )

# route 12: get temperatures based on city, start date and/or end date
@app.route('/api/temperatures/cities/<int:id_oras>', methods = ['GET'])
def get_city_temperatures(id_oras):
    try:
        # extract filter information (if any) from arguments
        start_date = request.args.get("from")
        end_date = request.args.get("until")

        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")

        # create a query with filter information
        query = {
            # add city id filter to query
            "id_oras" : id_oras
        }

         # add timestamp filter - start and/or end date(s) - to query
        if start_date and end_date:
            query["timestamp"] = {"$gte" : start_date, "$lte" : end_date}
        elif start_date:
            query["timestamp"] = {"$gte" : start_date}
        elif end_date:
            query["timestamp"] = {"$lte" : end_date}

        # apply the query on the temperatures collection
        temperatures = list(mongo.db.temperatures.find(query))

        result = [
            {
                "id" : t["id"],
                "valoare" : t["valoare"],
                "timestamp" : t["timestamp"].strftime("%Y-%m-%d")
            }
            for t in temperatures
        ]

        return Response(
            json.dumps(result, sort_keys = False),
            status = 200,
            mimetype = 'application/json'
        )

    except Exception as e:

        return Response(
            json.dumps({"error" : str(e)}),
            status = 500,
            mimetype = 'application/json'
        )


# route 13: get temperatures based on country, start date and/or end date
@app.route('/api/temperatures/countries/<int:id_tara>', methods = ['GET'])
def get_country_temperatures(id_tara):
    try:
        # extract filter information (if any) from arguments
        start_date = request.args.get("from")
        end_date = request.args.get("until")

        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")

        # extract cities from given country id
        cities = list(mongo.db.cities.find({"id_tara" : id_tara}))
        # extract ids of said cities
        cities_ids = [c["id"] for c in cities]

        # create a query with filter information
        query = {
            # add cities ids filter to query
            "id_oras" : {"$in" : cities_ids}
        }

        # add timestamp filter - start and/or end date(s) - to query
        if start_date and end_date:
            query["timestamp"] = {"$gte": start_date, "$lte": end_date}
        elif start_date:
            query["timestamp"] = {"$gte": start_date}
        elif end_date:
            query["timestamp"] = {"$lte": end_date}

        # apply the query on the temperatures collection
        temperatures = list(mongo.db.temperatures.find(query))

        result = [
            {
                "id": t["id"],
                "valoare": t["valoare"],
                "timestamp": t["timestamp"].strftime("%Y-%m-%d")
            }
            for t in temperatures
        ]

        return Response(
            json.dumps(result, sort_keys = False),
            status = 200,
            mimetype = 'application/json'
        )

    except Exception as e:

        return Response(
            json.dumps({"error" : str(e)}),
            status = 500,
            mimetype = 'application/json'
        )


# route 14: modify a temperature entry
@app.route('/api/temperatures/<int:id>', methods = ['PUT'])
def put_temperature(id):
    try:
        data = request.get_json()
        if not data:
            return Response(
                json.dumps({"error" : "invalid data, please include all required fields"}),
                status = 400,
                mimetype = 'application/json'
            )
        
        # verify the existence of all required fields for PUT request
        required_fields = ["id", "idOras", "valoare"]
        if not all (field in data for field in required_fields):
            return Response(
                json.dumps({"error" : "invalid data, please include all required fields"}),
                status = 400,
                mimetype = 'application/json'
            )
        
        # check if the required fields have the correct type
        if (
            not isinstance(data.get("id"), int) or 
            not isinstance(data.get("idOras"), int) or 
            not isinstance(data.get("valoare"), (float, int))
        ):
            return Response(
                json.dumps({"error" : "invalid data, please use correct data type for required fields"}),
                status = 400,
                mimetype = 'application/json'
            )
        
        # check if the request's id is valid for the route used
        if data.get("id") != id:
            return Response(
                json.dumps({"error" : "invalid data, please use the same id as in route"}),
                status = 400,
                mimetype = 'application/json'
            )
        
        # check if the city id is valid
        city_exists = mongo.db.cities.find_one({"id": data["idOras"]})
        if not city_exists:
            return Response(
                json.dumps({"error" : "city was not found"}),
                status = 404,
                mimetype = 'application/json'
            )
        
        result = mongo.db.temperatures.update_one(
            {"id" : id},
            {"$set" : {
                "id_oras" : data.get("idOras"),
                "valoare" : data.get("valoare")
            }}
        )

        if result.matched_count == 0:
            return Response(
                json.dumps({"error" : "temperature entry was not found"}),
                status = 404,
                mimetype = 'application/json'
            )
    
        return Response(status = 200)
    
    except Exception as e:
        if "duplicate key error" in str(e).lower():
            return Response(
                json.dumps({"error" : "there's already a temperature entry for this city and time"}),
                status = 409,
                mimetype = 'application/json'
            )
        
        return Response(
            json.dumps({"error" : str(e)}),
            status = 500,
            mimetype = 'application/json'
        )
    
# route 15: delete a temperature entry
@app.route('/api/temperatures/<int:id>', methods = ['DELETE'])
def delete_temperature(id):
    try:
        result = mongo.db.temperatures.delete_one(
            {"id" : id}
        )

        if result.deleted_count == 0:
            return Response(
                json.dumps({"error" : "temperature entry was not found"}),
                status = 404,
                mimetype = 'application/json'
            )
    
        return Response(status = 200)
    
    except Exception as e:
        return Response(
            json.dumps({"error" : str(e)}),
            status = 500,
            mimetype = 'application/json'
        )

if __name__ == '__main__':
    # run Mongo config
    try:
        configure_mongodb()
    except Exception as e:
        print(f"configure monogodb error: {e}\ntrying again...")
        time.sleep(5)
        configure_mongodb()

    # run Flask app
    app.run(host='0.0.0.0', debug=True)

