# Expedia — Part 1

## Repository and commit

GitHub repository:
[https://github.com/Meshal9993/expedia](https://github.com/Meshal9993/expedia)

Submitted commit:
74a9c7fcb727cb56eb615b54673eff04e51a75d0

## Implementation

Expedia uses Vue for the frontend, Python for the backend, and FastAPI for communication between them.

The user enters a hotel name in the Vue interface. The frontend sends the hotel-name search to FastAPI. The Python backend reads hotels.csv and trips.csv, connects the records using hotel\_id, and returns matching hotels with their available stays. Vue displays the returned results in a readable table.

## Verification

Successful search:

Action:
Search for Harbor Lantern Hotel.

Expected result:
The matching hotel and its available stays should appear.

Observed result:
Two stays appeared:

- Boston Harbor Weekend
- Boston Autumn Weekend

Screenshot:
[https://github.com/Meshal9993/expedia/blob/74a9c7fcb727cb56eb615b54673eff04e51a75d0/docs/screenshots/search-success.png](https://github.com/Meshal9993/expedia/blob/74a9c7fcb727cb56eb615b54673eff04e51a75d0/docs/screenshots/search-success.png)

No-results search:

Action:
Search for IST402.

Expected result:
A clear no-results message should appear.

Observed result:
The application displayed:
“No hotels found for ‘IST402’. Try another hotel name.”

Screenshot:
[https://github.com/Meshal9993/expedia/blob/74a9c7fcb727cb56eb615b54673eff04e51a75d0/docs/screenshots/search-no-results.png](https://github.com/Meshal9993/expedia/blob/74a9c7fcb727cb56eb615b54673eff04e51a75d0/docs/screenshots/search-no-results.png)

Additional verification:

- Frontend lint passed.
- Frontend production build passed.
- Browser console showed no warnings or errors.
- The supplied CSV files were unchanged.

## Project context and next steps

README:
[https://github.com/Meshal9993/expedia/blob/74a9c7fcb727cb56eb615b54673eff04e51a75d0/README.md](https://github.com/Meshal9993/expedia/blob/74a9c7fcb727cb56eb615b54673eff04e51a75d0/README.md)

AGENTS.md:
[https://github.com/Meshal9993/expedia/blob/74a9c7fcb727cb56eb615b54673eff04e51a75d0/AGENTS.md](https://github.com/Meshal9993/expedia/blob/74a9c7fcb727cb56eb615b54673eff04e51a75d0/AGENTS.md)

Design note:
[https://github.com/Meshal9993/expedia/blob/74a9c7fcb727cb56eb615b54673eff04e51a75d0/docs/design-note.md](https://github.com/Meshal9993/expedia/blob/74a9c7fcb727cb56eb615b54673eff04e51a75d0/docs/design-note.md)

Selected prompt:
[https://github.com/Meshal9993/expedia/blob/74a9c7fcb727cb56eb615b54673eff04e51a75d0/prompts/01-part1-hotel-search.md](https://github.com/Meshal9993/expedia/blob/74a9c7fcb727cb56eb615b54673eff04e51a75d0/prompts/01-part1-hotel-search.md)

Current handoff:
[https://github.com/Meshal9993/expedia/blob/74a9c7fcb727cb56eb615b54673eff04e51a75d0/handoffs/current.md](https://github.com/Meshal9993/expedia/blob/74a9c7fcb727cb56eb615b54673eff04e51a75d0/handoffs/current.md)

Remaining limitation:
The application currently reads travel data from CSV files only.

Next task:
Add persistent data storage and booking features.

