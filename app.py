from flask import Flask, jsonify, request, session
import itertools
import sqlite3

from storage import all_articles
from demographic_filtering import output
from content_filtering import get_recommendations

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vgu48rhg87thgreuh0tjhd985yt809e'


with sqlite3.connect("database.db") as con:
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, article_index INTEGER, liked_articles_indices TEXT, disliked_articles_indices TEXT)")



def get_next_correct_lang(arr, i):
    new_index = 0

    for x in arr[i:]:
        if x[14] == 'en':
            new_index = int(x[0])

            break
    
    return new_index



@app.route("/article")
def index():
    name = session.get('name')
    index = session.get('index')

    if name and (index != None):
        with sqlite3.connect("database.db") as con:
            cur = con.cursor()
            cur.execute("UPDATE users SET article_index = ? WHERE name = ?", (index, name))
            con.commit()

        lang = all_articles[index][14]


        if lang != 'en':
            new_index = get_next_correct_lang(all_articles, index)

            session['index'] = new_index
            index = new_index
        
        article_data = {
            "index": all_articles[index][0],
            "url": all_articles[index][11],
            "title": all_articles[index][12],
            "text": all_articles[index][13],
            "lang": all_articles[index][14],
            "total_events": all_articles[index][15]
        }

        return jsonify({
            "data": article_data,
            "status": "success"
        })

    else:
        return jsonify({
            "data": "user_not_logged_in",
            "status": "failure"
        })



@app.route("/auth", methods=['POST'])
def auth():
    name = request.args.get('name')
    session['name'] = name

    with sqlite3.connect("database.db") as con:
        cur = con.cursor()
        data = cur.execute("SELECT * FROM users WHERE name = ?", (name, )).fetchone()
        
        if data and data[1].strip().lower() == name.strip().lower():
            session['index'] = int(data[2])

        else:
            session['index'] = 0
            with sqlite3.connect("database.db") as con:
                cur = con.cursor()
                cur.execute("INSERT INTO users (name, article_index, liked_articles_indices, disliked_articles_indices) VALUES (?, ?, ?, ?)", (name, 0, '', ''))
                con.commit()

        return jsonify({'status': 'success'}), 201



@app.route("/like", methods=['POST'])
def like():
    name = session.get('name')
    index = session.get('index')

    if name and (index != None):
        with sqlite3.connect("database.db") as con:
            cur = con.cursor()
            data = cur.execute("SELECT * FROM users WHERE name = ?", (name, )).fetchone()[3]
            
            if len(data) == 0:
                data += str(index)
            else:
                data += ',' + str(index)
            
            session['index'] += 1
            index += 1
            cur.execute("UPDATE users SET article_index = ?, liked_articles_indices = ? WHERE name = ?", (index, data, name))
            con.commit()


        return jsonify({
            "status": "success"
        }), 201
    
    else:
        return jsonify({
            "data": "user_not_logged_in",
            "status": "failure"
        })



@app.route("/dislike", methods=['POST'])
def dislike():
    name = session.get('name')
    index = session.get('index')

    if name and (index != None):
        with sqlite3.connect("database.db") as con:
            cur = con.cursor()
            data = cur.execute("SELECT * FROM users WHERE name = ?", (name, )).fetchone()[4]
            
            if len(data) == 0:
                data += str(index)
            else:
                data += ',' + str(index)
            
            session['index'] += 1
            index += 1
            cur.execute("UPDATE users SET article_index = ?, disliked_articles_indices = ? WHERE name = ?", (index, data, name))
            con.commit()


        return jsonify({
            "status": "success"
        }), 201

    else:
        return jsonify({
            "data": "user_not_logged_in",
            "status": "failure"
        })



@app.route("/popular")
def popular():
    article_data = []

    for article in output:
        article_data.append({
            "url": article[0],
            "title": article[1],
            "text": article[2],
            "lang": article[3],
            "total_events": article[4]
        })

    return jsonify({
        "data": article_data,
        "status": "success"
    }), 200



@app.route("/recommendations")
def recommended():
    all_recommended = []
    liked_articles = []

    name = session.get('name')
    index = session.get('index')

    if name and (index != None):
        with sqlite3.connect("database.db") as con:
            cur = con.cursor()
            data = cur.execute("SELECT * FROM users WHERE name = ?", (name, )).fetchone()[3]
            liked_articles = data.split(',')

        
        for i in liked_articles:
            if i != '':
                article = all_articles[int(i)]

                for i in get_recommendations(article[4]):
                    if i[3] == 'en':
                        all_recommended.append(i)

        all_recommended.sort()
        all_recommended = list(all_recommended for all_recommended,_ in itertools.groupby(all_recommended))
        article_data = []

        for recommended in all_recommended:
            article_data.append({
                "url": recommended[0],
                "title": recommended[1],
                "text": recommended[2],
                "lang": recommended[3],
                "total_events": recommended[4]
            })
            
        return jsonify({
            "data": article_data,
            "status": "success"
        }), 200

    else:
        return jsonify({
            "data": "user_not_logged_in",
            "status": "failure"
        })
    


if __name__ == "__main__":
    app.run(debug=True)
