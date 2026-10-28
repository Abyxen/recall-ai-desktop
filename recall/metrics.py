import json


def dashboard(db):
    result = {}
    for key, query in {
        'documents': 'SELECT count(*) n FROM documents',
        'notebooks': 'SELECT count(*) n FROM (SELECT DISTINCT subject,notebook FROM documents)',
        'cards': 'SELECT count(*) n FROM cards',
        'due': "SELECT count(*) n FROM cards WHERE due<=date('now','localtime')",
        'reviews': 'SELECT count(*) n FROM reviews',
        'attempts': 'SELECT count(*) n FROM attempts',
    }.items():
        result[key] = db.rows(query)[0]['n']
    result['recent_documents'] = db.rows('SELECT * FROM documents ORDER BY id DESC LIMIT 6')
    result['recent_attempts'] = db.rows('SELECT a.*,q.title FROM attempts a JOIN quizzes q ON q.id=a.quiz_id ORDER BY a.id DESC LIMIT 8')
    activity = db.rows("""SELECT date(created,'localtime') day,count(*) n FROM
        (SELECT created FROM reviews UNION ALL SELECT created FROM attempts)
        WHERE date(created,'localtime')>=date('now','localtime','-6 days') GROUP BY day ORDER BY day""")
    result['activity'] = {row['day']: row['n'] for row in activity}
    topics = {}
    for attempt in db.rows('SELECT a.feedback,q.payload FROM attempts a JOIN quizzes q ON q.id=a.quiz_id ORDER BY a.id DESC LIMIT 100'):
        for feedback, item in zip(json.loads(attempt['feedback']), json.loads(attempt['payload'])):
            topics.setdefault(item['topic'], []).append(feedback['score'])
    result['weak_topics'] = sorted([(t, sum(v) / len(v), len(v)) for t, v in topics.items() if sum(v) / len(v) < .8], key=lambda r: r[1])[:8]
    return result
