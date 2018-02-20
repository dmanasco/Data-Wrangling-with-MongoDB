from pymongo import MongoClient

def insert_line(line, db):
    db.disneyworld.insert(line)

def insert_to_mongodb(filename, db):
    with open(filename) as f:
        for line in f:
            data = json.loads(line)
            insert_line(data,db)


client = MongoClient("mongodb://localhost:27017")
client.drop_database("disneyworld")
db = client.disneyworld

insert_to_mongodb("./DisneyWorld.osm.json", db)
print(db.disneyworld.find_one())