import os
from os.path import join, dirname
from dotenv import load_dotenv

from flask import (Flask, 
                   request, 
                   render_template, 
                   redirect, 
                   url_for, 
                   jsonify)
from pymongo import MongoClient
import requests
from datetime import datetime
from bson import ObjectId

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]
	
app = Flask(__name__)

@app.route('/')
def main():
    words_result = db.words.find({}, {'_id': False})
    words = []
    for word in words_result:
        definition = word['definitions'][0]['shortdef']
        definition = definition if type(definition) is str else definition[0]
        words.append({
            'word': word['word'],
            'definition': definition,
        })
    msg = request.args.get('msg')
    return render_template(
        'index.html',
        words=words,
        msg=msg
    )

@app.route('/detail/<keyword>')
def detail(keyword):
    api_key = '7ce36635-f726-4caa-9676-7c1a6b881728'
    url = f'https://www.dictionaryapi.com/api/v3/references/collegiate/json/{keyword}?key={api_key}'
    response = requests.get(url)
    definitions = response.json()

    if not definitions:
        suggested_words = ','.join(definitions)
        # diarahkan ke laman error dgn suggested words
        return redirect(url_for('error', suggested_words=suggested_words))

    if type(definitions[0]) is str:
        suggested_words = ','.join(definitions)
        return redirect(url_for('error', suggested_words=suggested_words))

    status = request.args.get('status_give', 'new')

    return render_template('detail.html', word=keyword, definitions=definitions, status=status)

@app.route('/error')
def error():
    # dapetin nilai suggested words
    suggested_words = request.args.get('suggested_words', '').split(',')
    return render_template('error.html', suggested_words=suggested_words)

# route untuk request CRUD
@app.route('/api/save_word', methods=['POST'])
def save_word():
    json_data = request.get_json()
    word = json_data.get('word_give')
    definitions = json_data.get('definitions_give')
    doc = {
        'word': word,
        'definitions': definitions,
        'date' : datetime.now().strftime('%d/%m/%Y'),
    }
    db.words.insert_one(doc)
    return jsonify({
        'result': 'success',
        'msg': f'the word, {word}, was saved!!!',
    })

@app.route('/api/delete_word', methods=['POST'])
def delete_word():
    word = request.form.get('word_give')
    # Hapus kata dari koleksi kata
    db.words.delete_one({'word': word})
    # Hapus contoh kalimat terkait dari koleksi contoh
    db.examples.delete_many({'word': word})
    return jsonify({
        'result': 'success',
        'msg': f'the word {word} was deleted'
    })

@app.route('/api/get_exs', methods=['GET'])
def get_exs():
    word = request.args.get('word')
    example_data = db.examples.find({'word': word})
    examples = []
    for example in example_data:
        examples.append({
            'id': str(example.get('_id')),
            'example': example.get('example')
        })
    return jsonify({'result': 'success', 'examples': examples})


@app.route('/api/save_axs', methods=['POST'])
def save_ex():
    word = request.form.get('word')
    example = request.form.get('example')
    doc = {
        'word': word,
        'example': example,
    }
    db.examples.insert_one(doc)
    return jsonify({
        'result': 'success',
        'msg': f'Your example, "{example}", for the word "{word}", was saved!'
        })

@app.route('/api/delete_axs', methods=['POST'])
def delete_ex():
    id = request.form.get('id')
    word = request.form.get('word')
    db.examples.delete_one({'_id': ObjectId(id)})
    return jsonify({
        'result': 'success',
        'msg': f'Your example for word, {word}, was deleted!'
    })


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)