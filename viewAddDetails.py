from findGeoAddress import *
from dbutils import *
from makeupdata import *
import json
class Accommodation:
    def __init__(self):
        self.id = None  # Unique identifier for the accommodation
        self.startDate = None
        self.endDate = None
        self.type = None
        self.beds = None
        self.bedrooms = None
        self.price = None
        self.address = None
        self.coordinates = None # (latitude, longitude)
        self.geoAddress = None
        self.isReserved = None
        self.averageRating = None
        self.ratingCount = None

    # Get the accommodation details
    def getDetails(self):
        return {
            "startDate": self.startDate,
            "endDate": self.endDate,
            "type": self.type,
            "beds": self.beds,
            "bedrooms": self.bedrooms,
            "price": self.price,
            "address": self.address,
            "coordinates": self.coordinates,
            "geoAddress": self.geoAddress,
            "isReserved": self.isReserved,
            "averageRating": self.averageRating,
            "ratingCount": self.ratingCount
        }
    
    def viewDetails(self):
        # Display accommodation details in a user-friendly format
        print(f"""Accommodation Details:\n
        Accommodation ID: {self.id}"\n
        Start Date: {self.startDate}\n
        End Date: {self.endDate}\n
        Type: {self.type}\n
        Beds: {self.beds}\n
        Bedrooms: {self.bedrooms}\n
        Price: {self.price}\n
        Address: {self.address}\n
        Coordinates: {self.coordinates}\n
        Geo Address: {self.geoAddress}\n
        Is Reserved: {self.isReserved}\n
        Average Rating: {self.averageRating}\n
        Rating Count: {self.ratingCount}""")
 
    def retrieveDetails(self, id):
        self.id = id
        result = get_accommodation_with_rating(id)
        if result:
            self.startDate = result["availability_start"]
            self.endDate = result["availability_end"]
            self.type = result["type"]
            self.beds = result["beds"]
            self.bedrooms = result["bedrooms"]
            self.price = result["price"]
            self.address = result["address"]
            self.setGeoAddress()
            self.isReserved = result["is_reserved"]
            self.averageRating = result["average_rating"]
            self.ratingCount = result["rating_count"]
        else:
            print("Accommodation not found.")
        return None

    def setGeoAddress(self):
        result = fetch_coordinates(self.address)[0]
        self.geoAddress, latitude, longitude  = getGeoAddress(json.loads(result.text))
        self.coordinates = (latitude, longitude)
        return None

    
def inputDetails():
    # Input accommodation details from the user
    accommodation = Accommodation()
    accommodation.startDate = input("Enter start date (YYYY-MM-DD): ")
    accommodation.endDate = input("Enter end date (YYYY-MM-DD): ")
    accommodation.type = str(input("Enter accommodation type: "))
    accommodation.beds = int(input("Enter number of beds: "))
    accommodation.bedrooms = int(input("Enter number of bedrooms: "))
    accommodation.price = float(input("Enter price: "))
    accommodation.address = str(input("Enter address: "))
    accommodation.setGeoAddress()
    return accommodation

if __name__ == "__main__":
    while True:
        test = str(input("Enter test type (testAdd/testRetrieve/testView/exit): "))
        match test:
            case "testAdd":
                # Example usage of adding accommodation details
                accommodation = inputDetails()
                # Add accommodation to the database
                accommodation.id = add_accommodation(
                    accommodation.startDate,
                    accommodation.endDate,
                    accommodation.type,
                    accommodation.beds,
                    accommodation.bedrooms,
                    accommodation.price,
                    accommodation.address,
                    accommodation.coordinates[0],
                    accommodation.coordinates[1],
                    accommodation.geoAddress
                )
                if( accommodation.id):
                    print(f"Accommodation successfully added with ID: {accommodation.id}.")
                    
            case "testRetrieve":
                # Example usage of retrieving accommodation details
                accommodation = Accommodation()
                id = int(input("Enter accommodation ID to retrieve: "))
                accommodation.retrieveDetails(id)
                accommodation.viewDetails()
            
            case "testView":
                # Example usage of viewing accommodation details
                accommodation = Accommodation()
                id = int(input("Enter accommodation ID to view: "))
                accommodation.retrieveDetails(id)
                accommodation.viewDetails()
            
            case "exit":
                print("Exiting...")
                break