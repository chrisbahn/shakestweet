import tweepy

twitter_consumer_key = open('static/secret/twitter_consumer_key.txt').read()
twitter_consumer_secret = open('static/secret/twitter_consumer_secret.txt').read()
twitter_access_token = open('static/secret/twitter_access_token.txt').read()
twitter_access_token_secret = open('static/secret/twitter_access_token_secret.txt').read()

auth = tweepy.OAuthHandler(twitter_consumer_key, twitter_consumer_secret)
auth.set_access_token(twitter_access_token, twitter_access_token_secret)

api = tweepy.API(auth)

public_tweets = api.home_timeline()
for tweet in public_tweets:
    print(tweet.text)

api = tweepy.API(auth)
# The line below does the actual Tweeting.
# api.update_status('Tomorrow and tomorrow and tomorrow...')
# api.update_status('Tomorrow and tomorrow and tomorrow...')

