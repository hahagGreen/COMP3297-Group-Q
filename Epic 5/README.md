### Epic 5 Document ###
There is one main directory, accommodations.

### 1. Accommodations ###
The Accommodations directory contains the API for updating the rating score from the UniHaven database. <br>
As mentioned in the backlog, this API would automatically update and re-calculate the average rating score of the particular accommodation. Then, it would return the up-to-date rating score in Json format

**Key Functions**
1. api_rate <br>
Endpoints: /accommodations/api_rate

| Method  | Parameters | Description |
| ------------- | ------------- | ------------- |
| POST  | 1. userId (Integer)<br> 2. accId (Integer) <br> 3. reservId (Integer) <br> 4. rating (Integer [0,5]) <br> 5. date  | The userId is for looking up the user in the database <br> The accId is for looking up the accommodation in the database. <br> The reservId acts as a foreign key for creating the rating object <br> Others are for creating the rating object |

***Sample Input and Output***
```
1. Valid User 
Input:
      accId = 49
      userId = 7
      reservId = 5
      rating = 4.00
      date = 2004-02-08
Endpoint: /accommodations/api_rate/
Output:
      {
  "status": "success",
  "message": "Rating updated successfully",
  "data": [
    {
      "rating_id": 41,
      "rating": 4,
      "date": "2025-04-14",
      "reservation": 5
    },
    {
      "average_rating": "4.00",
      "rating_count": 2
    }
  ]
}

```
