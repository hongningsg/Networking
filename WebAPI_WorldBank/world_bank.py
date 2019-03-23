import sqlite3
import requests
import json
import datetime
from flask import Flask, request, Response
from flask_restplus import Api, Resource, fields
db_name = 'data.db'
def create_db(db_file):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    try:
        c.execute('''CREATE TABLE collections (
                        collection_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        indicator TEXT,
                        indicator_value TEXT, 
                        creation_time TEXT)''')
        c.execute('''CREATE TABLE entries(
                        entry_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        collection_id INTEGER, 
                        country TEXT,
                        date TEXT,
                        value REAL,
                        FOREIGN KEY(collection_id) REFERENCES collections(collection_id)
                        )''')
        conn.commit()
    except:
        pass
    conn.close()
    db_name = db_file

'''
Put your API code below. No certain requriement about the function name as long as it works.
'''
app = Flask(__name__)
api = Api(app, version='1.0', title='World Bank',
    description='World bank collection',
)

resource_fields = api.model('Resource', {
     "indicator_id": fields.String,
})

base_url = 'http://api.worldbank.org/v2/countries/all/indicators/'
suffix = '?date=2013:2018&format=json&page='

def getEntity(payload, page):
    return requests.get(base_url + payload + suffix + str(page))

@api.response(200, 'OK')
@api.response(201, 'Created')
@api.response(404, 'Not found')
@api.route('/collections')
class Collection(Resource):
    def dict_factory(self, cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def AUTO_NOW(self):
        now = str(datetime.datetime.now())
        return now[:10] + 'T' + now[11:19] + 'Z'

    @api.doc(description='1- Import a collection from the data service')
    @api.expect(resource_fields)
    def post(self):
        payload = json.loads(request.data)['indicator_id']
        entity = json.loads(getEntity(payload, 1).text)
        try:
            page = entity[0]['page']
            entries_list = entity[1]
        except:
            return Response(status = 404, response = "Indicator Invalid!")
        conn = sqlite3.connect(db_name)
        conn.row_factory = self.dict_factory
        c = conn.cursor()
        c.execute("SELECT * FROM collections WHERE indicator = '%s'" % payload)
        collection = c.fetchone()
        status = 200
        if collection == None:
            indicator_value = entries_list[0]["indicator"]["value"]
            creation_time = self.AUTO_NOW()
            c.execute('INSERT INTO collections (indicator, indicator_value, creation_time) VALUES(?, ?, ?)',
                      (payload, indicator_value, creation_time))
            conn.commit()
            c.execute("SELECT * FROM collections WHERE indicator = '%s'" % payload)
            collection = c.fetchone()
            collection_id = collection['collection_id']
            for entry in entries_list:
                country = entry['country']['value']
                date = entry['date']
                value = entry['value']
                c.execute('INSERT INTO entries (collection_id, country, date, value) VALUES(?, ?, ?, ?)',
                          (collection_id, country, date, value))
            conn.commit()
            status = 201
        out = {
            "location" : "/collections/" + str(collection['collection_id']),
            "collection_id" : str(collection['collection_id']),
            "creation_time": collection['creation_time'],
            "indicator" : payload
        }
        conn.close()
        res = Response(status = status, response = json.dumps(out))
        res.headers["Content-type"] = "application/json"
        return res

    @api.doc(description='3 - Retrieve the list of available collections')
    def get(self):
        conn = sqlite3.connect(db_name)
        conn.row_factory = self.dict_factory
        c = conn.cursor()
        c.execute("SELECT * FROM collections")
        collections = c.fetchall()
        context = []
        for collection in collections:
            out = {
                "location": "/collections/" + str(collection['collection_id']),
                "collection_id": str(collection['collection_id']),
                "creation_time": collection['creation_time'],
                "indicator" : collection['indicator'],

            }
            context.append(out)
        conn.close()
        return Response(status=200, response=json.dumps(context, sort_keys=False,
                 indent=4, separators=(',', ': ')))

@api.response(200, 'OK')
@api.response(404, 'Not found')
@api.route('/collections/<collection_id>')
class CollectionID(Resource):
    def dict_factory(self, cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    @api.doc(description='2- Deleting a collection with the data service')
    def delete(self, collection_id):
        conn = sqlite3.connect(db_name)
        c = conn.cursor()
        collection_id = str(collection_id)
        c.execute("SELECT * FROM collections WHERE collection_id = %s" % collection_id)
        collection = c.fetchone()
        if collection == None:
            conn.close()
            errorMassage = "Collection (id = %s) is NOT exist!" % collection_id
            return Response(status=404, response=errorMassage)
        c.execute("DELETE FROM collections WHERE collection_id = %s" % collection_id)
        c.execute("DELETE FROM entries WHERE collection_id = %s" % collection_id)
        conn.commit()
        conn.close()
        context = {
            "message" : "Collection = " + collection_id + " is removed from the database!"
        }
        return Response(status=200, response=json.dumps(context))

    @api.doc(description='4 - Retrieve a collection')
    def get(self, collection_id):
        conn = sqlite3.connect(db_name)
        conn.row_factory = self.dict_factory
        c = conn.cursor()
        collection_id = str(collection_id)
        c.execute("SELECT * FROM collections WHERE collection_id = %s" % collection_id)
        collection = c.fetchone()
        if collection == None:
            conn.close()
            errorMassage = "Collection (id = %s) is NOT exist!" % collection_id
            return Response(status=404, response=errorMassage)
        context = {
            "collection_id": str(collection['collection_id']),
            "indicator": collection['indicator'],
            "indicator_value": str(collection['indicator_value']),
            "creation_time": collection['creation_time'],
        }
        c.execute("SELECT * FROM entries WHERE collection_id = %s" % collection_id)
        entries_db = c.fetchall()
        entries = []
        for entry in entries_db:
            entries.append({
                "country": entry['country'],
                "date": entry['date'],
                "value": str(entry['value'])
            })
        context["entries"] = entries
        conn.close()
        return Response(status=200, response=json.dumps(context, sort_keys=False,
                 indent=4, separators=(',', ': ')))

@api.response(200, 'OK')
@api.response(404, 'Not found')
@api.route('/collections/<collection_id>/<year>/<country>')
class YearCountry(Resource):
    def dict_factory(self, cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    @api.doc(description='5 - Retrieve economic indicator value for given country and a year')
    def get(self, collection_id, year, country):
        conn = sqlite3.connect(db_name)
        conn.row_factory = self.dict_factory
        c = conn.cursor()
        collection_id = str(collection_id)
        year = str(year)
        country = str(country)
        c.execute("SELECT * FROM collections WHERE collection_id = %s" % collection_id)
        collection = c.fetchone()
        if collection == None:
            conn.close()
            errorMassage = "Collection (id = %s) is NOT exist!" % collection_id
            return Response(status=404, response=errorMassage)
        indicator = collection['indicator']
        c.execute("SELECT * FROM entries WHERE collection_id = %s AND date = '%s'" % (collection_id, year))
        collection = c.fetchone()
        if collection == None:
            conn.close()
            errorMassage = "No result for year %s at Collection (id = %s)!" % (year, collection_id)
            return Response(status=404, response=errorMassage)
        c.execute("SELECT * FROM entries WHERE collection_id = %s AND date = '%s' AND country = '%s'" % (collection_id, year, country))
        collection = c.fetchall()
        if len(collection) == 0:
            conn.close()
            errorMassage = "No result for country %s in year %s at Collection (id = %s)!" % (country, year, collection_id)
            return Response(status=404, response=errorMassage)
        if len(collection) == 1:
            context = {
                "collection_id": collection_id,
                "indicator": indicator,
                "country": country,
                "year": year,
                "value": collection[0]['value']
            }
        else:
            context = []
            for col in collection:
                context.append({
                    "collection_id": collection_id,
                    "indicator": indicator,
                    "country": country,
                    "year": year,
                    "value": col['value']
                })
        conn.close()
        return Response(status=200, response=json.dumps(context, sort_keys=False,
                                                        indent=4, separators=(',', ': ')))

@api.response(200, 'OK')
@api.response(404, 'Not found')
@api.route('/collections/<collection_id>/<year>')
@api.doc(params={'q': 'query'})
class Query(Resource):
    def dict_factory(self, cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    @api.doc(description='6 - Retrieve top/bottom economic indicator values for a given year')
    def get(self, collection_id, year, query=None):
        request.args = request.args.to_dict()
        if len(request.args) > 0:
            if 'q' not in request.args:
                errorMassage = "Query should follow the format ?q=<query>" % collection_id
                return Response(status=404, response=errorMassage)
            query = request.args['q']
        conn = sqlite3.connect(db_name)
        conn.row_factory = self.dict_factory
        c = conn.cursor()
        collection_id = str(collection_id)
        year = str(year)
        c.execute("SELECT * FROM collections WHERE collection_id = %s" % collection_id)
        collection = c.fetchone()
        if collection == None:
            conn.close()
            errorMassage = "Collection (id = %s) is NOT exist!" % collection_id
            return Response(status=404, response=errorMassage)
        indicator = collection['indicator']
        indicator_value = collection['indicator_value']
        c.execute("SELECT * FROM entries WHERE collection_id = %s AND date = '%s'" % (collection_id, year))
        ets = c.fetchall()
        collection = []
        for e in ets:
            if e['value'] != None:
                collection.append(e)
        if len(collection) == 0:
            conn.close()
            errorMassage = "No result for year %s at Collection (id = %s)!" % (year, collection_id)
            return Response(status=404, response=errorMassage)
        conn.close()
        collection.sort(key=lambda entry: entry['value'], reverse=True)
        if query != None:
            query = str(query)
            istop = True
            if query[:3] == "top":
                number = query[3:]
            elif query[:6] == "bottom":
                number = query[6:]
                istop = False
            else:
                errorMassage = "Query must follow the format top<N> or bottom<N>!"
                return Response(status=404, response=errorMassage)
            if number.isdigit():
                number = int(number)
                if istop:
                    collection = collection[:number]
                else:
                    collection = collection[-number:]
            else:
                errorMassage = "Query in <N> must be a non-negative integer!"
                return Response(status=404, response=errorMassage)
        context = {
            "indicator": indicator,
            "indicator_value": indicator_value
        }
        entries = []
        for entry in collection:
            entries.append({
                "country": entry["country"],
                "date": entry["date"],
                "value": entry["value"]
            })
        context["entries"] = entries
        return Response(status=200, response=json.dumps(context, sort_keys=False,
                                                        indent=4, separators=(',', ': ')))
if __name__ == '__main__':
    create_db('data.db')
    app.run(debug=True)
