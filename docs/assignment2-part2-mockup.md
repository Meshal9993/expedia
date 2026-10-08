# Assignment 2 Part 2: chatbot mockup

Early layout retained and updated October 8, 2026 to match the implemented simple View.

```text
-----------------------------------------------------------
Booking — Ask about saved hotels
Answers use local records and simulated classroom rates/rooms.
Conversation ID: [saved backend ID]

Question
[ Which saved hotels in 02108 have rooms Oct 10–13? ] [ Ask ]
[ New conversation ] [ Reload history ]

Status: Loading... (Ask disabled while a request is pending)
-----------------------------------------------------------
Answer
[ Answer grounded in the retrieved local records           ]

[ Expand RAG Trace ]
Proposed SQL / Executed SQL / Parameters
Retrieved hotel/date records
Required-night checks and per-room totals in cents
-----------------------------------------------------------
[ Expand basic chat — preserved class checkpoint ]
-----------------------------------------------------------
```

States: idle, loading, answer, no matches, insufficient data, rejected query, service failure, and history-load failure. Empty successful retrieval differs from a failed/rejected query. Incomplete turns and truncated history are labelled.

The View uses labelled text inputs, native expandable details, keyboard focus, status messages, and escaped plain text. SQLite stores messages/traces; browser storage holds only the conversation ID. New conversation clears the browser reference, not saved history. ZIP search, Add/Remove, and list/map stay intact. No API key or raw provider error appears in the View.
