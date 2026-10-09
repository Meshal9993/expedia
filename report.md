# Expedia Lite — Part 2

## Repository and commit

Repository: https://github.com/Meshal9993/expedia

Final Part 2 commit: **dbdd20f3877e87e3f82769cc97ab1aa597dd299e**

## Implementation

Part 2 keeps the live ZIP hotel search and map from Part 1 and adds local saved hotel data and a RAG hotel assistant.

The Vue frontend lets the user search for hotels, save a hotel locally, see simulated nightly rates and room availability, and ask questions in the hotel assistant.

FastAPI connects the frontend to the backend. For hotel questions, the first LLM request creates a SQL query and parameters. The backend checks that the query is read-only, then SQLite returns the saved hotel records. A second LLM request uses those records to make the final answer.

The chatbot also shows a RAG Trace with the SQL, parameters, and retrieved records. Conversation history is saved in SQLite and stays after a page refresh.


## Verification

I tested the app in the browser using ZIP 16801.

The saved hotel was Courtyard by Marriott State College

I asked:

Any saved hotels in ZIP 16801 on 2026-10-14?

Expected: The assistant should use the saved local records and return the matching hotel.

Observed: The assistant returned the saved hotel using the SQLite records. The RAG Trace showed the proposed SQL, parameters, and retrieved records.

I also asked:

How much is Courtyard by Marriott State College on 2026-10-14?

Expected: The assistant should return the saved simulated nightly rate.

Observed: The assistant returned the rate from the saved data.

For a no match test, I asked:

Any saved hotels in ZIP 11111 on 2026-10-11?

Expected: No matching saved hotel should be returned.

Demo video: [Assignment 2 Part 2 Demo](docs/screenshots/assignment2-part2-demo.mov)

## Project context and next steps

Project files:

- [README](README.md)
- [AGENTS](AGENTS.md)
- [Design note](docs/design-note.md)
- [RAG research](docs/assignment2-part2-research.md)
- [Early mockup](docs/assignment2-part2-mockup.md)
- [RAG verification notes](docs/assignment2-part2-rag-context.md)
- [Hotel assistant prompt](prompts/hotel-assistant.md)
- [Current handoff](handoffs/current.md)

One limitation is that the hotel prices and room counts are test data and not real hotel information.

The main Part 2 work is complete.
