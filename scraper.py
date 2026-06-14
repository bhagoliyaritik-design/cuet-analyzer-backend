from flask import Flask, request, jsonify
from flask_cors import CORS
import os, requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

@app.route('/analyze', methods=['GET'])
def analyze():
    url = request.args.get('url').strip('"')
    if os.path.exists(url):
        try:
            with open(url, encoding='utf-8') as f:
                html = f.read()
        except UnicodeDecodeError:
            with open(url, encoding='latin1') as f:
                html = f.read()
    else:
        try:
            resp = requests.get(url)
            html = resp.text
        except:
            return jsonify({"error": "File not found or invalid URL."})

    soup = BeautifulSoup(html, 'html.parser')

    info_table = soup.find('table')
    if not info_table:
        return jsonify({"error": "No <table> found!"})
    rows = info_table.find_all('tr')
    if len(rows) < 3 or len(rows[0].find_all('td')) < 2:
        return jsonify({"error": "Table structure not expected for info."})

    application_no = rows[0].find_all('td')[1].text.strip()
    name = rows[1].find_all('td')[1].text.strip()
    roll_no = rows[2].find_all('td')[1].text.strip()

    subjects, total_score, total_questions = [], 0, 0
    section_divs = soup.find_all('div', class_='section-cntnr')
    for section_div in section_divs:
        section_lbl = section_div.find('div', class_='section-lbl')
        if not section_lbl: continue
        subject_name = section_lbl.find_all('span')[-1].text.strip()
        correct = incorrect = skipped = score = 0
        qtables = section_div.find_all('table', class_='questionRowTbl')
        for qtable in qtables:
            qrows = qtable.find_all('tr')
            for r in qrows:
                cells = r.find_all('td')
                if not cells or ('Q.' in cells[0].text):
                    continue
                labels = [c.text.strip().lower() for c in cells]
                if 'correct' in labels[-1]:
                    correct += 1; score += 5
                elif 'incorrect' in labels[-1]:
                    incorrect += 1; score -= 1
                else:
                    skipped += 1
        tot_q = correct + incorrect + skipped
        subjects.append({
            "name": subject_name,
            "score": score,
            "max_score": tot_q * 5,
            "correct": correct,
            "incorrect": incorrect,
            "skipped": skipped
        })
        total_score += score
        total_questions += tot_q

    return jsonify({
        "name": name,
        "application_no": application_no,
        "roll_no": roll_no,
        "total_score": total_score,
        "total_questions": total_questions,
        "subjects": subjects
    })

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
