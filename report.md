#  Booking — Part 2

## Repository and commit

Repository:
https://github.com/Meshal9993/expedia

Final commit:
23a94f768e3207bdcbd43a104449a9bd5ce3fc5c

For Part 2 I continued working on the same project from Part 1. I did the new work on the feature/part2-mvc-crud branch first, then after I finished testing it I merged it into main.


## Implementation

In Part 1 my app could search for a hotel and show the available stays. For Part 2 I added the booking part and booking history.

I used MVC for the project. The Vue frontend is the View because this is where the user searches, clicks buttons, makes a booking, and sees the history. In the backend I have models for hotels, trips, users, and bookings. I also added controllers for the database, search, and booking work.

The DatabaseController works with SQLite. It opens the database, creates the tables, checks the references between the data, and handles the CRUD operations. The BookingController handles the booking rules.

FastAPI is what connects the frontend to the backend.

The first time the database is made, the program uses the CSV files that were given to us. After that it uses SQLite. This way, if I make a new booking or cancel one, the change does not disappear when I restart the app.

For the frontend, I kept the hotel search from Part 1. I added a Book this stay button to the results. After choosing a stay, the user can choose one of the demo travelers and confirm the booking.

I also added Booking History. It includes booking ID, traveler, hotel, dates, and status. In case I cancel my booking, it will be saved in history, while the status will become Cancelled. I have also included an option to delete bookings for testing purposes.

## Verification

I tested the search first with Harbor Lantern Hotel. It showed two stays:

- Boston Harbor Weekend
- Boston Autumn Weekend

I also tried a hotel name that does not exist and the no-results message showed correctly.

Then I tested the booking process from the frontend. I created a booking and checked that it showed in Booking History. I tested cancelling it too. The booking was still there after I cancelled it, but the status changed to Cancelled.

I also created another test booking and deleted it from the frontend. After I confirmed the delete, it was removed from the history.

One problem I ran into while testing was that I deleted the test bookings, and later the local database had 0 bookings. The starter data did not come back because the database already had a seed marker. I reset only the local SQLite database and started the backend again. After that, the normal startup process added the original starter data again. The database had 8 hotels, 12 trips, 6 users, and 6 bookings.

After that I made a new booking, B007, and kept it for the restart test. Before restarting, the database had 7 bookings. I restarted both the backend and frontend, and B007 was still there. The database still had 8 hotels, 12 trips, 6 users, and 7 bookings. This showed that the changes were really being saved in SQLite and the starter data was not getting duplicated.

I also ran the automatic checks. The backend had 16 passing tests. The frontend lint passed and the production build passed. git diff --check also passed. The two warnings from the backend tests were dependency warnings and did not make any tests fail.

The original CSV files were not changed.


## Verification evidence

Search screenshot:

https://github.com/Meshal9993/expedia/blob/23a94f768e3207bdcbd43a104449a9bd5ce3fc5c/docs/screenshots/search-success.png

No results screenshot:

https://github.com/Meshal9993/expedia/blob/23a94f768e3207bdcbd43a104449a9bd5ce3fc5c/docs/screenshots/search-no-results.png

Part 2 video:

https://github.com/Meshal9993/expedia/blob/23a94f768e3207bdcbd43a104449a9bd5ce3fc5c/docs/screenshots/Recording%202026-09-21%20210541.mp4


## Project context

README:

https://github.com/Meshal9993/expedia/blob/23a94f768e3207bdcbd43a104449a9bd5ce3fc5c/README.md

AGENTS:

https://github.com/Meshal9993/expedia/blob/23a94f768e3207bdcbd43a104449a9bd5ce3fc5c/AGENTS.md

MVC contracts:

https://github.com/Meshal9993/expedia/blob/23a94f768e3207bdcbd43a104449a9bd5ce3fc5c/docs/mvc-contracts.md

Booking API prompt:

https://github.com/Meshal9993/expedia/blob/23a94f768e3207bdcbd43a104449a9bd5ce3fc5c/prompts/02-part2-booking-api.md

Booking View prompt:

https://github.com/Meshal9993/expedia/blob/23a94f768e3207bdcbd43a104449a9bd5ce3fc5c/prompts/03-part2-booking-view.md

Final verification prompt:

https://github.com/Meshal9993/expedia/blob/23a94f768e3207bdcbd43a104449a9bd5ce3fc5c/prompts/04-part2-final-verification.md

Current handoff:

https://github.com/Meshal9993/expedia/blob/23a94f768e3207bdcbd43a104449a9bd5ce3fc5c/handoffs/current.md
