# Assignment 2 Part 2: early chatbot mockup

Planning only; this interface is not implemented. It may change after the MVC/API contracts are agreed.

```text
-----------------------------------------------------------
Booking — Ask about saved hotels
Answers use local records and simulated classroom rates/rooms.

Question
[ Which saved hotels have rooms on October 12, 2026? ] [ Ask ]

Status: Loading... (Ask disabled while a request is pending)
-----------------------------------------------------------
Answer
[ Answer grounded in the retrieved local records           ]

Matched hotel/date information (optional)
Hotel name or "Name unavailable" | Date | Demo rate | Rooms
-----------------------------------------------------------
```

Planned states: idle, loading, answer, no matches, insufficient data, rejected query, and service failure. For example: "No saved hotel/date records match this question" or "The stored data cannot answer that question."

Show the simulated-data label beside rates and room counts. Keep a labelled text input, keyboard focus, and accessible status feedback. Existing ZIP search, local Add/Remove controls, and list/map selection stay intact. No API key or raw provider error appears in the View.
