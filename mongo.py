from flask_pymongo import PyMongo

# mongo_uri = "mongodb+srv://storageapp:Abhey123@cluster0.4xp0q36.mongodb.net/database"
mongo_uri = "mongodb+srv://storage:Abhey123@cluster0.i4dedvi.mongodb.net/database"

mongo = PyMongo()


def init_mongo(app):
    mongo.init_app(app)

# def test_mongodb_connection(uri):
#     try:
#         # Connect to the MongoDB cluster
#         client = MongoClient(uri)
#
#         # Access a test database
#         db = client.test
#
#         # Print the list of collections in the test database
#         print("Collections in the test database:")
#         print(db.list_collection_names())
#
#         # Close the connection
#         client.close()
#
#         return True
#     except Exception as e:
#         print("Error connecting to MongoDB:", e)
#         return False
#
#
# # Test the MongoDB connection
# if test_mongodb_connection(mongo_uri):
#     print("MongoDB connection test successful!")
# else:
#     print("MongoDB connection test failed!")
