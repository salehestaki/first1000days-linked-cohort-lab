# Exposure-window specification

For every child and each linked parent role, source event dates are assigned to one inclusive window:

| Window | Start | End |
|---|---|---|
| Preconception | conception − 365 days | conception − 1 day |
| Pregnancy | conception | birth |
| Postnatal 0–2 | birth + 1 day | birth + 730 days |

The windows are mutually exclusive. Event counts, binary exposure flags, and first event dates are produced in long and wide formats. An event exactly on conception is pregnancy exposure; an event exactly on birth is pregnancy exposure; an event exactly 730 days after birth is postnatal exposure.
