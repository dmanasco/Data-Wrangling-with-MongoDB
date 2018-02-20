from pymongo import MongoClient

lient = MongoClient("mongodb://localhost:27017")
client.drop_database("disneyworld")
db = client.disneyworld

db.disneyworld.count()

#count number of nodes
db.disneyworld.find({'type':'node'}).count()
#count number of ways
db.disneyworld.find({'type':'way'}).count()
#number of unique contributers to the dataset
len(db.disneyworld.distinct('created.user'))

#find top 5 users for the dataset
top_user = db.disneyworld.aggregate([{"$group":{"_id":"$created.user", "count":{"$sum":1}}}, {"$sort":{"count":-1}}, {"$limit":5}])
for line in top_user:
    print(line)

#find basic percentages of different types of users in the database
print("Percentage of items by top submitter (Brian@Brea) - "+"{0:.2f}".format(db.disneyworld.find({"created.user":"Brian@Brea"}).count()/db.disneyworld.count()*100)+"%")
print("Percentage of top two sumbitters (Brian@Brea, NE2) - "+"{0:.2f}".format(db.disneyworld.find({"created.user": { "$in" : ["Brian@Brea", "NE2"]}}).count()/db.disneyworld.count()*100)+"%")
print("Percentage of top five sumbitters - "+"{0:.2f}".format(db.disneyworld.find({"created.user": { "$in" : ["Brian@Brea", "NE2", "3yoda", "Mongo Poker", "Di?genes de Sinope"]}}).count()/db.disneyworld.count()*100)+"%")

#find all theme_parks within the dataset
themeParks = db.disneyworld.find({"tourism": "theme_park", "name" : {"$exists" : "true"}}, {"name": 1, "operator" : 1, "_id" : 0})
themeParks = themeParks.sort([("operator", 1), ("name", 1)])
for row in themeParks:
    print(row)

#find all attractions within the dataset
attractions = db.disneyworld.find({"tourism": "attraction", "name" : {"$exists" : "true"}}, {"name": 1, "_id":0})
for row in attractions:
    print(row)

#find rollercoasters in database
rollerCoasters = db.disneyworld.find({"tourism" : "attraction", "attraction" : "roller_coaster"}, {"name" : 1, "_id": 0})
for line in rollerCoasters:
    print(line)

#find out what is under cunstruction in the database.
underConstruction = db.disneyworld.find({"landuse" : "construction", "name" : { "$exists": "true", "$ne": "null" }}, {"name" : 1, "_id" : 0})
for line in underConstruction:
    print(line)

#find shops on Main Street in Magic Kingdom
mainstreet = db.disneyworld.find({"address.street" : "Main Street", "name" : { "$exists": "true", "$ne": "null" }}, {"name": 1, "_id":0})
for line in mainstreet:
    print(line)

#find all fast_food restauraunts in the dataset
fastfood = db.disneyworld.find({"amenity" : "fast_food", "name" : { "$exists": "true", "$ne": "null" }}, {"name": 1, "_id":0})
for line in fastfood:
    print(line)

hotels = db.disneyworld.find({"tourism" : "hotel", "name" : { "$exists": "true", "$ne": "null" }}, {"name": 1, "_id":0})
print("There are "+str(hotels.count())+ " hotels within the dataset")
for line in hotels.sort("name", 1):
    print(line)

#returns the top 5 cuisines for restaurants in the dataset
for i in db.disneyworld.aggregate([{"$match":{"amenity":{"$exists":1}, "amenity":"restaurant",
                                    "cuisine" : { "$exists": "true", "$ne": "null" }}}, 
                                   {"$group":{"_id":"$cuisine", "count":{"$sum":1}}},{"$sort":{"count":-1}},
                                   {"$limit" : 5}]):
    print(i)

#identify 2 documents with the same name
for i in db.disneyworld.find({"name" : "Epcot"}, {"node_refs": 0, "_id" : 0}):
    print(i)


