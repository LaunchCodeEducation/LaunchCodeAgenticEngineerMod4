---
classification: internal
project: proj-lessons
doc_type: lesson
---

# Authentication Does Not Guarantee Scrape Access

## What happened

During MarketRadar's Facebook Marketplace work, establishing or restoring an authenticated session did not by itself make scraping reliable. A session could appear authenticated while the automated browser still failed to receive or expose the listing content expected by the scraper.

## What we learned

Authentication and scrape access are separate checkpoints. A successful login only proves that authentication succeeded; it does not prove that an automated browser can reliably access and extract marketplace listings.

## Future application

Test authentication and listing extraction independently. After establishing a session, explicitly verify that the expected listing elements and data are available before treating the source as ready for scraping.
