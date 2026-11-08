Get status bar today​
Copy link
Auth Required

Returns the total coding time for today. Used by editor plugins to display the status bar widget.
Path Parameters

    id
    Copy link to id
    Type: string
    required

    User ID or "current"

Responses

    200

    successful
    application/json
    401

    unauthorized

Request Example for get/api/hackatime/v1/users/{id}/statusbar/today
Python http.client

import http.client

conn = http.client.HTTPSConnection("hackatime.hackclub.com")

headers = {
"Authorization": "Bearer YOUR_SECRET_TOKEN"
}

conn.request(
"GET",
"/api/hackatime/v1/users/%7Bid%7D/statusbar/today?api_key=YOUR_SECRET_TOKEN",
headers=headers,
)

response = conn.getresponse()
print(response.read().decode())

conn.close()

Test Request(get /api/hackatime/v1/users/{id}/statusbar/today)
Status: 200
Status: 401

{
"data": {
"grand_total": {
"total_seconds": 7200,
"text": "2h 30m / 4h goal"
},
"goal": {
"target_seconds": 14400,
"tracked_seconds": 9000,
"completion_percent": 62,
"complete": false
}
}
}

successful
Get last 7 days stats​
Copy link
Auth Required

Returns coding statistics for the last 7 days. Used by some WakaTime dashboards.
Responses

    200

    successful
    application/json
    401

    unauthorized

Request Example for get/api/hackatime/v1/users/current/stats/last_7_days
Python http.client

import http.client

conn = http.client.HTTPSConnection("hackatime.hackclub.com")

headers = {
"Authorization": "Bearer YOUR_SECRET_TOKEN"
}

conn.request(
"GET",
"/api/hackatime/v1/users/current/stats/last_7_days?api_key=YOUR_SECRET_TOKEN",
headers=headers,
)

response = conn.getresponse()
print(response.read().decode())

conn.close()

Test Request(get /api/hackatime/v1/users/current/stats/last_7_days)
Status: 200
Status: 401

{
"data": {
"username": "U0266FRGP",
"user_id": "U0266FRGP",
"start": "2024-03-13T00:00:00Z",
"end": "2024-03-20T23:59:59Z",
"status": "ok",
"total_seconds": 25200,
"daily_average": 3600,
"days_including_holidays": 7,
"range": "last_7_days",
"human_readable_range": "Last 7 Days",
"human_readable_total": "7 hrs 0 mins",
"human_readable_daily_average": "1 hrs 0 mins",
"is_coding_activity_visible": true,
"is_other_usage_visible": true,
"editors": [
{
"name": "VS Code",
"total_seconds": 25200,
"percent": 100,
"digital": "7:00:00",
"text": "7 hrs 0 mins",
"hours": 7,
"minutes": 0,
"seconds": 0
}
],
"languages": [
{
"name": "Ruby",
"total_seconds": 18000,
"percent": 71.43,
"digital": "5:00:00",
"text": "5 hrs 0 mins",
"hours": 5,
"minutes": 0,
"seconds": 0
}
],
"machines": [
{
"name": "Orpheus-MacBook-Pro",
"total_seconds": 25200,
"percent": 100,
"digital": "7:00:00",
"text": "7 hrs 0 mins",
"hours": 7,
"minutes": 0,
"seconds": 0
}
],
"projects": [
{
"name": "hackatime",
"total_seconds": 21600,
"percent": 85.71,
"digital": "6:00:00",
"text": "6 hrs 0 mins",
"hours": 6,
"minutes": 0,
"seconds": 0
}
],
"operating_systems": [
{
"name": "Mac",
"total_seconds": 25200,
"percent": 100,
"digital": "7:00:00",
"text": "7 hrs 0 mins",
"hours": 7,
"minutes": 0,
"seconds": 0
}
],
"categories": [
{
"name": "coding",
"total_seconds": 25200,
"percent": 100,
"digital": "7:00:00",
"text": "7 hrs 0 mins",
"hours": 7,
"minutes": 0,
"seconds": 0
}
]
}
}

successful
