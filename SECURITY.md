# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

Vi tar säkerhet på allvar. Om du upptäcker en säkerhetsrisk, vänligen kontakta oss direkt:

- **Email**: security@voltsecurity.io
- **Response Time**: Vi strävar efter att svara inom 48 timmar

### Vad du ska inkludera:
- Beskrivning av sårbarheten
- Steg för att återskapa problemet
- Potentiell påverkan
- Föreslag på lösning (om du har någon)

### Vad händer sen:
1. Vi bekräftar mottagandet inom 48 timmar
2. Vi utvärderar och bekräftar sårbarheten
3. Vi arbetar på en lösning
4. Vi släpper en patch och krediterar dig (om du önskar)

## Säkerhetsåtgärder i projektet

- `.env` filer är gitignorerade och innehåller känslig konfiguration
- Ingen hårdkodad credentials
- Alla dokument i `data/inbox/` gitignoreras för att skydda känsliga fakturor
- Loggfiler gitignoreras

## Bästa praxis

- Använd aldrig produktionsdata i utvecklingsmiljö
- Håll `.env` säker och dela aldrig denna fil
- Uppdatera dependencies regelbundet
- Använd starka lösenord för databaser och tjänster
