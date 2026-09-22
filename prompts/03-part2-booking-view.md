# Part 2 Vue booking View

Continue on `feature/part2-mvc-crud` and preserve Part 1 hotel search. Follow the MVC contracts: Vue owns presentation, interaction, CSS, HTTP calls, and display state; controllers own booking rules and persistence; the View never reads SQLite or CSV files.

Add a clear “Book this stay” action to every search result without booking immediately. When selected, show the hotel and stay, allow selection of one supplied demo traveler, and provide a Confirm Booking action that sends `POST /api/bookings`, displays success or failure, and shows the generated booking ID without reloading the page.

Add Booking History with an optional demo-traveler filter. Show booking ID, traveler, hotel, stay, dates, and status. Allow confirmed bookings to be cancelled through `PATCH /api/bookings/{booking_id}` while retaining the cancelled row. Provide an explicit, confirmed Delete action for temporary test bookings using `DELETE /api/bookings/{booking_id}`. Handle empty history, no search results, missing bookings, and failed create/cancel/delete requests with readable messages.

Keep the layout original and simple, using the existing project screenshots only for continuity and hierarchy. Clearly separate Hotel Search, Search Results, Make a Booking, and Booking History. Do not add authentication, payments, surge pricing, database access, or unrelated features. Run frontend lint/build, the complete backend tests, and—when available—an automated browser smoke test that creates, finds, cancels, and deletes only a newly created temporary booking. Do not commit until reviewed.
