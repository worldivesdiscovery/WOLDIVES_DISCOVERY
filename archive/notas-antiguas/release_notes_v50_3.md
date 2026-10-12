# WORLDIVES DISCOVERY v50.3

- PDF generation reverted to the built-in PDF generator so the application does not require ReportLab/Pillow to be installed separately.
- Kept the existing QR generation through the already-declared `qrcode` dependency.
- Kept reservation, authentication, booking, payment, centre, diver and admin logic unchanged.
- Receipt endpoints `/api/bookings/{id}/receipt` and `/api/bookings/{id}/receipt.pdf` remain compatible.
- Diver sheet endpoint `/api/bookings/{id}/diver-sheet.pdf` remains compatible.
