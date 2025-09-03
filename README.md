# Requirment Description
###### Create a Python microservice that ingests sales‑call transcripts, stores them durably, and serves actionable conversation analytics through a small REST API.

### Ingestion process
- Call huggingface API to get the transcript of the sales call.
- Huggingface API:
```bash
curl --location 'https://datasets-server.huggingface.co/rows?dataset=MohammadOthman%2Fmo-customer-support-tweets-945k&config=default&split=train&offset=2&limit=2'
```
### Response
```json
{
  "rows": [
            {
                "output": "We understand your concerns and we would like for you to please send us a Direct Message, so that we can further assist you.",
                "input": "Since I signed up with you....Since day 1"
            }
  ],
  "total": 0,
  "limit": 0,
  "offset": 0
}
```
- Using aiohttp for async calls
- Validate the transcript data. And store the json.
- Pushed into celery queue for sentiment,talk ratio,embeddings processing. 
- Max 3 retries for status like on status code, limit exceed, timeout calls.
- Handling the Concurrent request on API.
- request timeout handling.
#### Classes
- Ingest -> creating the singleton class for ingestion.
- Transcript -> abstract class for transcript.(Can use different strategies for different transcript dataset)
- HuggingFaceTranscript -> concrete class for HuggingFace transcript dataset.
- Session -> singleton class for aiohttp session.
#### Note
- polling the API using offset and limit.
- Storing json in same directory for now. Can be changed to any durable storage.
- This ingestion process is scheduled to run after every X min.
- celery process managing the scheduled Ingestion Process.

### Data storage 
- Using sqlite(for demo) for durable storage(can be replaced by postgres or any other).
#### Model
- Call
  - id: primary key
  - agent_id: foreign key(reference to Agent table)(index)
  - customer_id: 
  - agent_talk_ratio -> (processed and stored by celery worker(Insight Processor))
  - customer_sentiment_score -> (processed and stored by celery worker(Insight Processor))
  - embeddings -> (processed and stored by celery worker(Insight Processor))
  - customer_transcript -> Text - (full text search index)
  - agent_transcript -> Text

- Agent(summary statistics -> for agent leaderboard, updated by celery worker(Insight Processor)
  - id: primary key 
  - avg_talk_ratio: 
  - total_calls: 
  - avg_sentiment_score:
- Relations
  - One to Many relation between Agent and Call table.

### Insight Processor(cal sentiment score talk ratio and embeddings for each call fetch by Ingestion Process)
- cal agent talk ratio, customer sentiment score, embedding(models - SentenceTransformer, sentiment-analysis).
- Run Transaction to Update the Call table with these insights.
- Run Transaction to Update the Agent table with summary statistics.
- Using celery worker for processing the insights.
#### Note
- Handling update on Agent table using transaction and row level lock(select for update).
- Retry and transaction time out.
- using sqlalchemy ORM.

### Celery
- scheduling the Ingestion Process Periodically.
- Async processing of insights Processor(fetched data process).
- Off load the data processing task from Ingestion Process.
- Using redis as a broker.
- Celery - worker consume the task from the queue and invoke the data process.
- Retry for process data and failed scheduling.

### REST API(FastAPI)
- Serving Processed data through REST API.
- API Endpoints (jwt authentication)

signin to generate token
```bash
curl --location 'http://127.0.0.1:8000/signin' \
--header 'Content-Type: application/json' \
--header 'Cookie: csrftoken=yZI1GpMeX2RhBNrlxGwGbHI8rHXAPKXu' \
--data '{
    "name":"rahul"
}'
```
#### response
```bash
{
    "name": "rahul",
    "token": "jwt token"
}
```
query processed calls with filters
```bash
curl --location 'http://127.0.0.1:8000/api/v1/calls/' \
--header 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoicmFodWwiLCJleHAiOjE3NTY4NjI4ODQuMDM5MTU3fQ.Q42Sxzqi5ZI0NF6r37kalpXcnKK1FiHDtIdJHaIIkW8' \
--header 'Cookie: csrftoken=yZI1GpMeX2RhBNrlxGwGbHI8rHXAPKXu'
```
#### response
```bash
{
    "total": 1,
    "offset": 1,
    "limit": 10,
    "data": [
        {
            "call_id": "63896ecf-5859-48f7-8bc6-cddcc0ce3b9d",
            "agent_id": "9d54ae6e-ddd0-4f3a-86ce-52899582f2f8",
            "customer_id": "6d8e2882-7170-45ac-9916-4adb62322a0e",
            "language": "en",
            "start_time": "2025-09-02",
            "duration_seconds": 177,
            "transcript_customer": "y’all lie about your “great” connection. 5 bars LTE, still won’t load something. Smh.",
            "transcript_agent": "H there! we would definitely like to work with you on this, how long have you been eeriencing this issue?",
            "agent_talk_ratio": 0.59,
            "customer_sentiment_score": -1.0,
            "embeddings": "[-0.01, -0.04]"
        }
    ]
}
```

get call by id
```bash
curl --location 'http://127.0.0.1:8000/api/v1/calls/63896ecf-5859-48f7-8bc6-cddcc0ce3b9d' \
--header 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoicmFodWwiLCJleHAiOjE3NTY4NjI4ODQuMDM5MTU3fQ.Q42Sxzqi5ZI0NF6r37kalpXcnKK1FiHDtIdJHaIIkW8' \
--header 'Cookie: csrftoken=yZI1GpMeX2RhBNrlxGwGbHI8rHXAPKXu'
```
#### response
```bash
{
    "call_id": "63896ecf-5859-48f7-8bc6-cddcc0ce3b9d",
    "agent_id": "9d54ae6e-ddd0-4f3a-86ce-52899582f2f8",
    "customer_id": "6d8e2882-7170-45ac-9916-4adb62322a0e",
    "language": "en",
    "start_time": "2025-09-02",
    "duration_seconds": 177,
    "transcript_customer": "y’all lie about your “great” connection. 5 bars LTE, still won’t load something. Smh.",
    "transcript_agent": "H there! we would definitely like to work with you on this, how long have you been eeriencing this issue?",
    "agent_talk_ratio": 0.59,
    "customer_sentiment_score": -1.0,
    "embeddings": "[-0.01, -0.04]"
}
```
get agent leaderboard(avg_sentiment_score,avg_talk_ratio,total_calls)
```bash
curl --location 'http://127.0.0.1:8000/api/v1/analytics/agents' \
--header 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoicmFodWwiLCJleHAiOjE3NTY4NjI4ODQuMDM5MTU3fQ.Q42Sxzqi5ZI0NF6r37kalpXcnKK1FiHDtIdJHaIIkW8' \
--header 'Cookie: csrftoken=yZI1GpMeX2RhBNrlxGwGbHI8rHXAPKXu'
```
response
```bash
[
    {
            "agent_id": "8f85a71b-c72c-4846-91e0-925d41d6b43b",
            "total_calls": 1,
            "avg_talk_ratio": 0.95,
            "avg_sentiment_score": 1.0
        },
        {
            "agent_id": "d7b9479f-9b18-46fe-9727-ae2835fc0149",
            "total_calls": 1,
            "avg_talk_ratio": 0.88,
            "avg_sentiment_score": 1.0
        }
]
```

similar calls based on embeddings
```bash
curl --location 'http://127.0.0.1:8000/api/v1/calls/971bdcb1-b993-4dc4-9eb8-2335242fd85d/recommendations' \
--header 'Authorization: Bearer eyJhbGciOiJIUzI1NsInR5cCI6IkpXVCJ9.eyJuYW1lIjoicmFodWwiLCJleHAiOjE3NTY4NjI4ODQuMDM5MTU3fQ.Q42Sxzqi5ZI0NF6r37kalpXcnKK1FiHDtIdJHaIIkW8' \
--header 'Cookie: csrftoken=yZI1GpMeX2RhBNrlxGwGbHI8rHXAPKXu'
```
response
```bash
{
    "call_id": "971bdcb1-b993-4dc4-9eb8-2335242fd85d",
    "similar_calls": [
        {
            "call_id": "c42dd98e-e415-44b0-b74d-d0739b821db0",
            "transcript_agent": "Hi there, sorry about that. Please message me when you visited the store and I will look into this. Thanks Kirsty",
            "transcript_customer": "so fed up of this very familiar sight at Houghton Regis. Get more staff amp stock the place properly. This is just a small example"
        },
        {
            "call_id": "9ee09860-8b34-4fc0-b170-e87a616976cd",
            "transcript_agent": "Hi there, sorry about that. Please message me when you visited the store and I will look into this. Thanks Kirsty",
            "transcript_customer": "so fed up of this very familiar sight at Houghton Regis. Get more staff amp stock the place properly. This is just a small example"
        },
        {
            "call_id": "d3ab2745-8075-494e-9c78-3f1606faa308",
            "transcript_agent": "Hi there, sorry about that. Please message me when you visited the store and I will look into this. Thanks Kirsty",
            "transcript_customer": "so fed up of this very familiar sight at Houghton Regis. Get more staff amp stock the place properly. This is just a small example"
        },
        {
            "call_id": "e0964127-4de8-4ccc-9474-4948138c0b55",
            "transcript_agent": "Would you please message the Adobe Product amp your purchase details that you have so that we can ask our eerts to follow up. Raj",
            "transcript_customer": "did not work. Tried it on another computer, fresh install, same thing..."
        },
        {
            "call_id": "ce0044b1-0911-4d45-86bc-98676c716370",
            "transcript_agent": "Would you please message the Adobe Product amp your purchase details that you have so that we can ask our eerts to follow up. Raj",
            "transcript_customer": "did not work. Tried it on another computer, fresh install, same thing..."
        }
    ],
    "coaching_nudges": [
        "hello",
        "hi",
        "hey"
    ]
}
```
## Run locally with Docker
Follow the steps below to run the application using Docker.

#### clone repo
```bash
git clone https://github.com/rahulp2020/Call-Analytics.git
cd Call-Analytics
```

#### build docker image and install dependencies
```bash
docker-compose build
```

#### run the container
```bash
docker-compose up
```

#### verify Running Containers
```bash
docker ps
```

# Access the FastAPI Endpoints

#### stop the container
```bash
docker-compose down
```
  



