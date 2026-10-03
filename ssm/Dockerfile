# Pobieramy oficjalnego Pythona
FROM python:3.10-slim

# Tworzymy i przechodzimy do katalogu roboczego
WORKDIR /app

# Kopiujemy listę wymaganych bibliotek
COPY requirements.txt .

# Instalujemy biblioteki
RUN pip install --no-cache-dir -r requirements.txt

# Kopiujemy resztę plików projektu do kontenera
COPY . .

# Wskazujemy port, na którym aplikacja nasłuchuje
EXPOSE 8080

# Uruchomienie aplikacji przez Gunicorn (wymagane dla Flaska na produkcji)
CMD ["gunicorn", "ssm:app", "--bind", "0.0.0.0:8080"]
