"""
Inits the summary bot. It starts a Reddit instance using PRAW, gets the latest posts
and filters those who have already been processed.
"""

import praw
import requests
import tldextract

import cloud
import config
import scraper
import summary

# We don't reply to posts which have a very small or very high reduction.
MINIMUM_REDUCTION_THRESHOLD = 20
MAXIMUM_REDUCTION_THRESHOLD = 68

# File locations
POSTS_LOG = "./processed_posts.txt"
WHITELIST_FILE = "./assets/whitelist.txt"
ERROR_LOG = "./error.log"

# Templates.
TEMPLATE = open("./templates/es.txt", "r", encoding="utf-8").read()


HEADERS = {"User-Agent": "Summarizer v2.0"}


def load_whitelist():
    """Reads the processed posts log file and creates it if it doesn't exist.

    Returns
    -------
    list
        A list of domains that are confirmed to have an 'article' tag.

    """

    with open(WHITELIST_FILE, "r", encoding="utf-8") as log_file:
        return log_file.read().splitlines()


def load_log():
    """Reads the processed posts log file and creates it if it doesn't exist.

    Returns
    -------
    list
        A list of Reddit posts ids.

    """

    try:
        with open(POSTS_LOG, "r", encoding="utf-8") as log_file:
            return log_file.read().splitlines()

    except FileNotFoundError:
        with open(POSTS_LOG, "a", encoding="utf-8") as log_file:
            return []


def update_log(post_id):
    """Updates the processed posts log with the given post id.

    Parameters
    ----------
    post_id : str
        A Reddit post id.

    """

    with open(POSTS_LOG, "a", encoding="utf-8") as log_file:
        log_file.write("{}\n".format(post_id))


def log_error(error_message):
    """Updates the error log.

    Parameters
    ----------
    error_message : str
        A string containing the faulty url and the exception message.

    """

    with open(ERROR_LOG, "a", encoding="utf-8") as log_file:
        log_file.write("{}\n".format(error_message))


def init():
    """Inits the bot."""

    reddit = praw.Reddit(client_id=config.APP_ID, client_secret=config.APP_SECRET,
                         user_agent=config.USER_AGENT, username=config.REDDIT_USERNAME,
                         password=config.REDDIT_PASSWORD)

    processed_posts = load_log()
    whitelist = load_whitelist()

    for subreddit in config.SUBREDDITS:

        for submission in reddit.subreddit(subreddit).new(limit=50):

            if submission.id not in processed_posts:

                clean_url = submission.url.replace("amp.", "")
                ext = tldextract.extract(clean_url)
                domain = "{}.{}".format(ext.domain, ext.suffix)

                if domain in whitelist:

                    try:
                        with requests.get(clean_url, headers=HEADERS, timeout=10) as response:

                            # Most of the times the encoding is utf-8 but in edge cases
                            # we set it to ISO-8859-1 when it is present in the HTML header.
                            if "iso-8859-1" in response.text.lower():
                                response.encoding = "iso-8859-1"
                            elif response.encoding == "ISO-8859-1":
                                response.encoding = "utf-8"

                            html_source = response.text

                        article_title, article_date, article_body = scraper.scrape_html(
                            html_source)

                        summary_dict = summary.get_summary(article_body)
                    except Exception as e:
                        log_error("{},{}".format(clean_url, e))
                        update_log(submission.id)
                        print("Failed:", submission.id)
                        continue

                    # To reduce low quality submissions, we only process those that made a meaningful summary.
                    if summary_dict["reduction"] >= MINIMUM_REDUCTION_THRESHOLD and summary_dict["reduction"] <= MAXIMUM_REDUCTION_THRESHOLD:

                        # Create a wordcloud, upload it to Imgur and get back the url.
                        image_url = cloud.generate_word_cloud(
                            summary_dict["article_words"])

                        # We start creating the comment body.
                        post_body = "\n\n".join(
                            ["> " + item for item in summary_dict["top_sentences"]])

                        top_words = ""

                        for index, word in enumerate(summary_dict["top_words"]):
                            top_words += "{}^#{} ".format(word, index+1)

                        post_message = TEMPLATE.format(
                            article_title, clean_url, summary_dict["reduction"], article_date, post_body, image_url, top_words)

                        reddit.submission(submission).reply(post_message)
                        update_log(submission.id)
                        print("Replied to:", submission.id)
                    else:
                        update_log(submission.id)
                        print("Skipped:", submission.id)


if __name__ == "__main__":

    init()
