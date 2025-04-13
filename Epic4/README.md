### Epic 3 Document ###
There are two main directories, accommodations and specialist for different purposes.

### 1. Accommodations ###
The Accommodations directory contains the API for fetching the accommodation details from the UniHaven database. <br>
As mentioned in the backlog, this API would automatically fetch data from the database with the primary key, id of the accommodations. After that, the API would return a list of the details of the particular accommodation in Json formatting

**Key Functions**
1. api_view <br>
Endpoints: /accommodations/api_view

| Method  | Parameters | Description |
| ------------- | ------------- | ------------- |
| GET  | 1. accId (Integer)  | The accId is for looking up the accommodations in the database| 
| POST  | 1. userId (Integer)  | The userId is for looking up the user in the database |

***Sample Input and Output***
```
1. Valid User 
Input:
      accId = 1
      userId = 1
Endpoint: /accommodations/api_view?accId=1
Output:
      {
  "accommodation_id": 1,
  "type": "Flat",
  "availability_start": "2026-06-05",
  "availability_end": "2027-08-29",
  "beds": 2,
  "bedrooms": 1,
  "price": "20240.39",
  "address": "72 Madison Road, B/11, North Point, Hong Kong",
  "latitude": 22.252767916077374,
  "longitude": 114.11877208616524,
  "geo_address": "72 Madison Road, B/11, North Point, Hong Kong",
  "is_reserved": true
      }

2. Invalid User (Not exist in the database)
Input:
      accId = 1
      userId = 20000
Endpoints: /accommodations/api_view?accId=1
Output:
      {
  "error": "User not found"
      }
```
### 2. Specialist ###
The specialist directory contain the APIs for the operations done by the specialist, including adding and editing the accommodations details to the system and also the UniHaven database. <br>
As mentioned in the backlog, these APIs would accept the input details from the specialist and update the current database with the latest information.

**Key Functions**
1. api_add <br>
Endpoints: /accommodations/api_add/ <br>

| Method  | Parameters | Description |
| ------------- | ------------- | ------------- |
| POST | 1. userId (Integer) <br> 2. startDate (String YYYY-MM-DD) <br> 3. endDate (String YYYY-MM-DD) <br> 4. type (String) <br> 5. beds (Integer) <br> 6. bedrooms (Integer) <br> 7. price (Number) <br> 8. address (String) <br>| The userId is for looking up the user in the database <br> The others are the details for the accommodation  |

***Sample Input and Output***
```
1. Valid User and Details of accommodations
Input:
      userId = 1
      startDate = 2005-02-05
      endDate = 2024-02-08
      type = hall
      beds = 3
      bedsroom = 2
      price = 12344
      address = The University of Hong Kong
Endpoint : /specialist/api_add/
Output:
      {
  "accommodation_id": 105,
  "type": "hall",
  "availability_start": "2005-02-05",
  "availability_end": "2024-02-08",
  "beds": 3,
  "bedrooms": 2,
  "price": "12312313.00",
  "address": "The University of Hong Kong",
  "latitude": 22.2828,
  "longitude": 114.13771,
  "geo_address": "3223115988T20050430",
  "is_reserved": false
      }

2. Invalid User (Not exist in the database)
Input:
      userId = 20000
     --Details of accommodation are neglected--
Endpoints: /accommodations/api_add/
Output:
      {
  "error": "User not found"
      }
```
<br>
2. api_edit <br>
Endpoints: /accommodations/api_edit/

| Method  | Parameters | Description |
| ------------- | ------------- | ------------- |
| POST | 1. userId (Integer) <br> 2. startDate (String YYYY-MM-DD) <br> 3. endDate (String YYYY-MM-DD) <br> 4. type (String) <br> 5. beds (Integer) <br> 6. bedrooms (Integer) <br> 7. price (Number) <br> 8. address (String) <br> 9. accId (Integer)| The userId is for looking up the user in the database <br> The others are the updated details for the accommodation <br> The accId is for looking up the accommodations in the database |

***Sample Input and Output***
```
1. Valid User, Valid Accommodation and Updated Details of accommodations
Input:
      userId = 1
      accId = 103
      startDate = 2005-02-05
      endDate = 2024-02-08
      type = hall
      beds = 3
      bedsroom = 2
      price = 12344
      address = The University of Hong Kong
Endpoint : /specialist/api_add/
Output:
      {
  "accommodation_id": 103,
  "type": "hall",
  "availability_start": "2005-02-05",
  "availability_end": "2024-02-08",
  "beds": 3,
  "bedrooms": 2,
  "price": "12312313.00",
  "address": "The University of Hong Kong",
  "latitude": 22.2828,
  "longitude": 114.13771,
  "geo_address": "3223115988T20050430",
  "is_reserved": false
      }

2. InValid User (Not exist in the database)
Input:
      userId = 20000
     --Details of accommodation are neglected--

Endpoint : /specialist/api_add/
Output:
      {
  "error": "User not found"
}

3. Non-specialist User
Input:
      userId = 7  (Who is a student)
      --Details of accommodation are neglected--
Endpoint : /specialist/api_add/
Output:
      {
      "error": "You cannot access to this as you are not a specialist"
      }
```
