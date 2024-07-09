import os
from flask import Flask, jsonify
from datetime import datetime, timedelta
import psycopg2
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

app = Flask(__name__)

# Configuration de la connexion à PostgreSQL
db_config = {
    "host": os.environ.get("primary.thyroresearch-ddb--kl8x797qxrg2.addon.code.run"),
    "port": os.environ.get("29647"),
    "database": os.environ.get("pubmed"),
    "user": os.environ.get("_6865d85393a52a7f"),
    "password": os.environ.get("_e5407dde3a89a0756343cba1a7eaf1")
}

def get_db_connection():
    conn = psycopg2.connect(**db_config)
    return conn

def get_articles_of_previous_day():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        previous_date = (datetime.now() - timedelta(days=1)).date()
        query = """
        SELECT a.pmid, a.title, a.entrez_date, 
               au.lastname, 
               c.condition, c.category, 
               pt.population_type, 
               pbt.publication_type
        FROM articles a
        LEFT JOIN authors au ON a.pmid = au.pmid
        LEFT JOIN conditions c ON a.pmid = c.pmid
        LEFT JOIN population_type pt ON a.pmid = pt.pmid
        LEFT JOIN publication_type pbt ON a.pmid = pbt.pmid
        WHERE a.entrez_date = %s
        """
        cur.execute(query, (previous_date,))
        articles = cur.fetchall()
        cur.close()
        conn.close()
        combined_data = []
        for row in articles:
            article = {
                'pmid': row[0],
                'title': row[1],
                'entrez_date': row[2],
                'lastname': row[3],
                'condition': row[4],
                'category': row[5],
                'population_type': row[6],
                'publication_type': row[7]
            }
            combined_data.append(article)
        return combined_data
    except Exception as e:
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
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
else:
    gunicorn_app = app