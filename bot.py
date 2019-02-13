"""
Inits the summary bot. It starts a Reddit instance using PRAW, gets the latest posts
and filters those who have already been processed.
"""
import praw
import requests
import tldextract
from bs4 import BeautifulSoup

import config
import summary


# We don't reply to posts which have a very small reduction.
MINMUM_REDUCTION_THRESHOLD = 20

# We don't process articles smaller than this.
ARTICLE_MINIMUM_LENGTH = 650

# File locations
POSTS_LOG = "./processed_posts.txt"
WHITELIST_FILE = "./whitelist.txt"
ERROR_LOG = "./error.log"

# Header and Footer templates.
HEADER = """### {} \n\nReducido en un {:.2f}%\n\n*****\n\n"""
FOOTER = """*****\n\n*^Este ^bot ^solo ^responde ^cuando ^logra ^resumir ^en ^un ^mínimo ^del ^20%. ^Este ^bot ^se ^encuentra ^en ^fase ^de ^pruebas, ^tus ^sugerencias ^y ^comentarios ^son ^bienvenidos. ​*\n\n[Nota Original]({}) | [GitHub](https://git.io/fhQkC) | {}"""


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
        return log_file.write("{}\n".format(post_id))


def log_error(error_message):
    """Updates the error log.

    Parameters
    ----------
    error_message : str
        A string containing the faulty url and the exception message.

    """

    with open(ERROR_LOG, "a", encoding="utf-8") as log_file:
        return log_file.write("{}\n".format(error_message))


def init():
    """Inits the bot."""

    reddit = praw.Reddit(client_id=config.APP_ID, client_secret=config.APP_SECRET,
                         user_agent=config.USER_AGENT, username=config.REDDIT_USERNAME,
                         password=config.REDDIT_PASSWORD)

    processed_posts = load_log()
    whitelist = load_whitelist()

    for submission in reddit.subreddit(config.SUBREDDIT).new():

        if submission.id not in processed_posts:

            ext = tldextract.extract(submission.url)
            domain = "{}.{}".format(ext.domain, ext.suffix)

            if domain in whitelist:

                try:
                    article, title = extract_article_from_url(submission.url)
                    summary_dict = summary.get_summary(article, title)
                except Exception as e:
                    log_error("{},{}".format(submission.url, e))
                    update_log(submission.id)
                    print("Failed:", submission.id)
                    continue

                post_body = ""

                for sentence in summary_dict["top_sentences"]:
                    post_body += """> {}\n\n""".format(sentence)

                top_words = ""

                for index, word in enumerate(summary_dict["top_words"]):
                    top_words += "{}^#{} ".format(word, index+1)

                post_message = HEADER.format(
                    summary_dict["title"], summary_dict["reduction"]) + post_body + FOOTER.format(submission.url, top_words)

                # To reduce low quality submissions, we only process those that made a meaningful summary.
                if summary_dict["reduction"] >= MINMUM_REDUCTION_THRESHOLD:
                    reddit.submission(submission).reply(post_message)
                    update_log(submission.id)
                    print("Replied to:", submission.id)


def extract_article_from_url(url):
    """Tries to scrape the article from the given url.

    Parameters
    ----------
    url : str
        The url of the article.

    Returns
    -------
    tuple
        The article text and its title.

    """

    headers = {"User-Agent": "Summarizer v0.2"}

    with requests.get(url, headers=headers) as response:

        # Sometimes Requests makes an incorrect guess, we force it to use utf-8
        if response.encoding == "ISO-8859-1":
            response.encoding = "utf-8"

        html_source = response.text

    # We create a BeautifulSOup object and remove the unnecessary tags.
    # We also apply a little hack to make sure paragraphs are separated.
    soup = BeautifulSoup(html_source.replace("</p>", "</p>\n"), "html5lib")
    [tag.extract() for tag in soup.find_all(["script", "img", "a", "time", "h1"])]

    for tag in soup.find_all("div"):

        try:
            if "image" in tag["id"] or "img" in tag["id"] or "video" in tag["id"] or "hidden" in tag["id"]:
                tag.extract()
        except:
            pass

    for tag in soup.find_all("div"):

        try:
            tag_class = "".join(tag["class"])

            if "image" in tag_class or "img" in tag_class or "video" in tag_class:
                tag.extract()
        except:
            pass

    # Then we extract the title and the article tags.
    title = soup.find("title").text.replace("\n", " ").strip()

    article = ""

    # Sometimes we have more than one article tag. We are going to grab the longest one.
    for article_tag in soup.find_all("article"):

        if len(article_tag.text) >= len(article):
            article = article_tag.text

    # The article is too short, let's try to find it in another tag.
    if len(article) <= ARTICLE_MINIMUM_LENGTH:

        for tag in soup.find_all(["div", "section"]):

            try:
                if "artic" in tag["id"] or "summary" in tag["id"] or "cont" in tag["id"] or "note" in tag["id"]:
                    # We guarantee to get the longest div.
                    if len(tag.text) >= len(article):
                        article = tag.text
            except:
                pass

    # The article is still too short, let's try one more time.
    if len(article) <= ARTICLE_MINIMUM_LENGTH:

        for tag in soup.find_all(["div", "section"]):

            try:
                tag_class = "".join(tag["class"])

                if "artic" in tag_class or "summary" in tag_class or "cont" in tag_class or "note" in tag_class:

                    # We guarantee to get the longest div.
                    if len(tag.text) >= len(article):
                        article = tag.text
            except:
                pass

    # We give up If the article is too short.
    if len(article) <= 100:
        raise Exception("No article found.")

    return article, title


if __name__ == "__main__":

    init()
