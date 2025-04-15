### Epic 4: ###

### 1. Specialist ###
The specialist directory contains APIs for reservation management, including cancellation and viewing active reservations. These APIs ensure specialists can efficiently manage accommodations and reservations.

---

**Key Functions**  
1. **api_active**  
Endpoint: `/specialist/api_active`  

| Method  | Parameters | Description |  
| ------------- | ------------- | ------------- |  
| GET  | None  | Returns all active reservations with "confirmed" or "pending" status |  

***Sample Input and Output***  
```
1. Valid Request  
Endpoint: /specialist/api_active  
Output:  
{
  "reservations": [
    {
      "reservation_id": 13,
      "username": "Courtney Wilson",
      "email": "student83@connect.hku.hk",
      "address": "31 Thomas Shores, C/6, Sai Wan, Hong Kong",
      "status": "confirmed",
      "user": 88,
      "accommodation": 13
    },
    {
      "reservation_id": 22,
      "username": "Amy Mcfarland",
      "email": "student45@connect.hku.hk",
      "address": "32 Garcia Harbors, D/24, North Point, Hong Kong",
      "status": "pending",
      "user": 50,
      "accommodation": 60
    },
  ]
}
```

2. **api_cancel**
Endpoint: `/specialist/api_cancel`

| Method  | Parameters | Description |  
| ------------- | ------------- | ------------- |  
| GET  | reservation_id (Integer)  | Cancels a reservation if status is "confirmed" or "pending". |

***Sample Input and Output***
```
1. Valid Cancellation  
Input:  
      reservation_id = 45  

Endpoint: /specialist/api_cancel?reservation_id=45  
Output:  
{
  "message": "Reservation Canceled"
}
```

```
2. Invalid Reservation ID  
Input:  
      reservation_id = NULL
Output:  
{
  "error": "Reservation ID not provided"
}
```
