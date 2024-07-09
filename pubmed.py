from flask import Flask, jsonify
from datetime import datetime
import psycopg2
from apscheduler.schedulers.background import BackgroundScheduler
import time

app = Flask(__name__)

# Configuration de la connexion à PostgreSQL
db_config = {
    "host": "primary.thyroresearch-ddb--kl8x797qxrg2.addon.code.run",
    "port": "29647",
    "database": "pubmed",
    "user": "_6865d85393a52a7f",
    "password": "_e5407dde3a89a0756343cba1a7eaf1"
}

def get_db_connection():
    conn = psycopg2.connect(
        host=db_config['host'],
        port=db_config['port'],
        database=db_config['database'],
        user=db_config['user'],
        password=db_config['password']
    )
    return conn

def get_articles_of_the_day():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        today_date = datetime.now().date()

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
        cur.execute(query, (today_date,))

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

@app.route('/get-today-articles', methods=['GET'])
def get_today_articles():
    articles = get_articles_of_the_day()
    return jsonify(articles)

def scheduled_task():
    articles = get_articles_of_the_day()
    print("Articles du jour récupérés:", articles)

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(scheduled_task, 'cron', hour=6, minute=0)
    scheduler.start()

    try:
        app.run(debug=True)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
