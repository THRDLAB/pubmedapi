import os
from flask import Flask, jsonify
from datetime import datetime, timedelta
import psycopg2
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

app = Flask(__name__)

# Configuration de la connexion à PostgreSQL
conn = psycopg2.connect(
    host="primary.thyroresearch-ddb--kl8x797qxrg2.addon.code.run",
    port="29647",
    database="pubmed",
    user="_6865d85393a52a7f",
    password="_e5407dde3a89a0756343cba1a7eaf1"
)

def get_articles_of_previous_day():
    try:
        cur = conn.cursor()

        # Obtenez la dernière date d'entrez dans la base de données
        cur.execute("SELECT MAX(entrez_date) FROM articles")
        last_entrez_date = cur.fetchone()[0]

        if last_entrez_date is None:
            print("Aucune date d'entrez trouvée.")
            return []

        query = """
        SELECT 
            a.pmid, 
            a.title, 
            a.entrez_date,
            STRING_AGG(DISTINCT au.lastname, ', ') AS authors,
            STRING_AGG(DISTINCT c.condition, ', ') AS conditions,
            STRING_AGG(DISTINCT c.category, ', ') AS categories,
            STRING_AGG(DISTINCT pt.population_type, ', ') AS population_types,
            STRING_AGG(DISTINCT pbt.publication_type, ', ') AS publication_types
        FROM articles a
        LEFT JOIN authors au ON a.pmid = au.pmid
        LEFT JOIN conditions c ON a.pmid = c.pmid
        LEFT JOIN population_type pt ON a.pmid = pt.pmid
        LEFT JOIN publication_type pbt ON a.pmid = pbt.pmid
        WHERE a.entrez_date = %s
        GROUP BY a.pmid, a.title, a.entrez_date
        """
        cur.execute(query, (last_entrez_date,))
        articles = cur.fetchall()

        cur.close()

        combined_data = []
        for row in articles:
            article = {
                'pmid': row[0],
                'title': row[1],
                'entrez_date': row[2],
                'authors': row[3],
                'conditions': row[4],
                'categories': row[5],
                'population_types': row[6],
                'publication_types': row[7]
            }
            combined_data.append(article)

        return combined_data

    except psycopg2.Error as e:
        print(f"Erreur lors de la récupération des articles: {e}")
        return []

@app.route('/')
def home():
    return "Bienvenue sur l'API PubMed. Utilisez /get-previous-day-articles pour obtenir les articles de la veille."

@app.route('/get-previous-day-articles', methods=['GET'])
def get_previous_day_articles():
    articles = get_articles_of_previous_day()
    return jsonify(articles)

def scheduled_task():
    with app.app_context():
        articles = get_articles_of_previous_day()
        print("Articles de la veille récupérés:", articles)

scheduler = BackgroundScheduler()
scheduler.add_job(func=scheduled_task, trigger=CronTrigger(hour=6, minute=0))
scheduler.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
else:
    gunicorn_app = app
