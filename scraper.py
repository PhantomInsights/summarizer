"""
This function tries to extract the article title, date and body from an HTML string.
"""

from datetime import datetime

from bs4 import BeautifulSoup

# We don't process articles that have fewer characters than this.
ARTICLE_MINIMUM_LENGTH = 650


def scrape_html(html_source):
    """Tries to scrape the article from the given HTML source.

    Parameters
    ----------
    html_source : str
        The html source of the article.

    Returns
    -------
    tuple
        The article title, date and body.

    """

    # Very often the text between tags comes together, we add an artificial newline to each common tag.
    for item in ["</p>", "</blockquote>", "</div>", "</h3>", "<br>"]:
        html_source = html_source.replace(item, item+"\n")

    # We create a BeautifulSOup object and remove the unnecessary tags.
    soup = BeautifulSoup(html_source, "html5lib")

    # Then we extract the title and the article tags.
    article_title = soup.find("title").text.replace("\n", " ").strip()

    # If our title is too short we fallback to the first h1 tag.
    if len(article_title) <= 5:
        article_title = soup.find("h1").text.replace("\n", " ").strip()

    article_date = ""

    # We look for the first meta tag that has the word 'time' in it.
    for item in soup.find_all("meta"):

        if "time" in item.get("property", ""):

            clean_date = item["content"].split("+")[0].replace("Z", "")
            
            # Use your preferred time formatting.
            article_date = "{:%d-%m-%Y a las %H:%M:%S}".format(
                datetime.fromisoformat(clean_date))
            break

    # If we didn't find any meta tag with a datetime we look for a 'time' tag.
    if len(article_date) <= 5:
        try:
            article_date = soup.find("time").text.strip()
        except:
            pass

    # We remove some tags that add noise.
    [tag.extract() for tag in soup.find_all(
        ["script", "img", "ol", "ul", "time", "h1", "h2", "h3", "iframe", "style", "form", "footer", "figcaption"])]

    # These class names/ids are known to add noise or duplicate text to the article.
    noisy_names = ["image", "img", "video", "subheadline", "editor", "fondea", "resumen", "tags", "sidebar", "comment",
                   "entry-title", "breaking_content", "pie", "tract", "caption", "tweet", "expert", "previous", "next",
                   "compartir", "rightbar", "mas", "copyright", "instagram-media", "cookie", "paywall", "mainlist", "sitelist"]

    for tag in soup.find_all("div"):

        try:
            tag_id = tag["id"].lower()

            for item in noisy_names:
                if item in tag_id:
                    tag.extract()
        except:
            pass

    for tag in soup.find_all(["div", "p", "blockquote"]):

        try:
            tag_class = "".join(tag["class"]).lower()

            for item in noisy_names:
                if item in tag_class:
                    tag.extract()
        except:
            pass

    # These names commonly hold the article text.
    common_names = ["artic", "summary", "cont", "note", "cuerpo", "body"]

    article_body = ""

    # Sometimes we have more than one article tag. We are going to grab the longest one.
    for article_tag in soup.find_all("article"):

        if len(article_tag.text) >= len(article_body):
            article_body = article_tag.text

    # The article is too short, let's try to find it in another tag.
    if len(article_body) <= ARTICLE_MINIMUM_LENGTH:

        for tag in soup.find_all(["div", "section"]):

            try:
                tag_id = tag["id"].lower()

                for item in common_names:
                    if item in tag_id:
                        # We guarantee to get the longest div.
                        if len(tag.text) >= len(article_body):
                            article_body = tag.text
            except:
                pass

    # The article is still too short, let's try one more time.
    if len(article_body) <= ARTICLE_MINIMUM_LENGTH:

        for tag in soup.find_all(["div", "section"]):

            try:
                tag_class = "".join(tag["class"]).lower()

                for item in common_names:
                    if item in tag_class:
                        # We guarantee to get the longest div.
                        if len(tag.text) >= len(article_body):
                            article_body = tag.text
            except:
                pass

    return article_title, article_date, article_body
