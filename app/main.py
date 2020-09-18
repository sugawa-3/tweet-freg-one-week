from flask import Flask, jsonify, make_response, request, render_template
from requests_oauthlib import OAuth1Session
import json
from forms import SearchForm, DownloadForm
import os
import datetime
import re
from io import StringIO
import csv

app = Flask(__name__)

app.config['base_json_url'] = 'https://api.twitter.com/1.1/%s.json'
app.config['search_url'] = app.config['base_json_url'] % ('search/tweets')

app.config['twitter'] = OAuth1Session(
    os.environ.get("TWITTER_API_CONSUMER_KEY"),
    os.environ.get("TWITTER_API_CONSUMER_SECRET"),
    os.environ.get("TWITTER_API_ACCESS_TOKEN"),
    os.environ.get("TWITTER_API_ACCESS_TOKEN_SECRET")
)

app.config['default_search_word'] = 'シガーロス'

app.secret_key = os.urandom(24)


@app.route('/', methods=['GET', 'POST'])
def index():

    form = SearchForm(request.form)

    if form.search_word.data == '':
        form.search_word.data = app.config['default_search_word']

    tweets = searchTweets(form.search_word.data)

    oneweek_tweet_counts = {}
    oneweek = create_oneweek()
    for i in oneweek:
        oneweek_tweet_counts[i] = 0

    oneweek_tweet_counts = get_oneweek_tweet_counts(tweets, oneweek, oneweek_tweet_counts)

    while True:
        next_results_id = exists_next_results(tweets)
        if next_results_id is False:
            break
        tweets = searchTweets(form.search_word.data, next_results_id)
        oneweek_tweet_counts = get_oneweek_tweet_counts(tweets, oneweek, oneweek_tweet_counts)

    counts = []
    for i in oneweek_tweet_counts:
        counts.append(str(oneweek_tweet_counts.get(i, 0)))

    num_counts = []
    for i in oneweek_tweet_counts:
        num_counts.append(oneweek_tweet_counts.get(i, 0))
    total = sum(num_counts)

    return render_template('index.html', form=form, counts=counts, total=total, oneweek=oneweek)


@app.route('/download', methods=['POST'])
def csv_download():

    form = DownloadForm(request.form)

    f = StringIO()
    writer = csv.writer(f, quotechar='"', lineterminator="\n")

    writer.writerow(['検索ワード', form.search_word.data])
    writer.writerow(['合計1週間のツイート数', form.total.data])
    writer.writerow(['1週間毎のツイート数'])
    writer.writerow(covert_string_to_array(form.oneweek.data))
    writer.writerow(covert_string_to_array(form.counts.data))

    res = make_response()
    res.data = f.getvalue().encode('cp932', 'ignore')
    res.headers['Content-Type'] = 'text/csv'
    res.headers['Content-Disposition'] = \
        'attachment; filename=' +\
        datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S') +\
        '-oneweek-tweet.csv'

    return res


def searchTweets(search_word, next_results_id=None):
    params = {
        'q': '#'+search_word+' -filter:retweets',
        'lang': 'ja',
        'locale': 'ja',
        'result_type': 'recent', #最新のツイート
        'count': 100,
        'max_id': next_results_id
    }

    response = app.config['twitter'].get(app.config['search_url'], params=params)
    return json.loads(response.text)


def get_oneweek_tweet_counts(search_api_response, oneweek, oneweek_tweet_counts,):

    if 'statuses' in search_api_response:
        for statuses in search_api_response['statuses']:
            created_at = convert_datetime(statuses['created_at'])
            if created_at in oneweek:
                oneweek_tweet_counts[created_at] += 1
    return oneweek_tweet_counts


def exists_next_results(search_api_response):
    next_results_id = None
    if 'search_metadata' in search_api_response:
        if 'next_results' in search_api_response['search_metadata']:
            next_results_id = re.findall(
                '\?max_id=(\d*)',
                search_api_response['search_metadata']['next_results']
            )

    if next_results_id is None:
        return False

    return next_results_id[0]


def create_oneweek():
    today = datetime.datetime.now()
    oneweek = [today.strftime('%Y-%m-%d')]
    for i in range(6):
        today -= datetime.timedelta(days=1)
        oneweek.append(today.strftime('%Y-%m-%d'))
    oneweek.reverse()
    return oneweek


def convert_datetime(date_time):
    strp_date_time = datetime.datetime.strptime(date_time, "%a %b %d %H:%M:%S %z %Y")
    return datetime.datetime.strftime(strp_date_time, '%Y-%m-%d')


def covert_string_to_array(str):
    str = re.sub(r"[\[\]']", "", str)
    array = str.split(",")
    return array


@app.errorhandler(Exception)
def handle_exception(e):
    return render_template("500.html"), 500


if __name__ == '__main__':
     app.run(app.run(host='0.0.0.0', debug=False, port=5000))
