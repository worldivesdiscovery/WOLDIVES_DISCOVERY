# WORLDIVES DISCOVERY — v50.1 PDF fix

- Fixed the reservation receipt PDF query: user phone numbers live in `user_profiles`, not `users`.
- Fixed the operational diver-sheet PDF query for the same schema issue.
- Kept the previous `/api/bookings/{id}/receipt` endpoint for compatibility.
- Added `/api/bookings/{id}/receipt.pdf` as the canonical PDF endpoint.
- Updated customer-facing PDF links in Mi área / Reserva to use the `.pdf` endpoint.
- Added receipt + QR and operational PDF actions to the center reservation view.
- PDF generation validated as a readable 1-page PDF with QR using a representative booking fixture.
- Existing authorization is preserved: owners can access their own reservation documents; centers can access reservations belonging to their center; administrators retain access.
