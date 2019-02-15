"""
This script extracts and ranks the sentences and words of an article.
"""
from collections import Counter

from nltk import tokenize

# The number of sentences we need.
NUMBER_OF_SENTENCES = 5

# The number of top words we need.
NUMBER_OF_TOP_WORDS = 5

# Multiplier for uppercase and long words.
IMPORTANT_WORDS_MULTIPLIER = 3

# The minimum number of characters needed for a line to be valid.
LINE_LENGTH_THRESHOLD = 150

# It is very important to add spaces on these words.
# Otherwise it will take into account partial words.
COMMON_WORDS = [
    ",", "|", "-", "‘", "’", ";", "(", ")", ".", ":", "¿", "?", '“', '”', '"', "'", "•",
    " Un ", " Una ", " El ", " La ", " Los ", " Las ", " Y ", " A ", " O ", " Si ", " No ", " Su ",
    " En ", " Foto ", " Video ", " De ", " Va ", " Como ", " Cuando ", " Que ", " Por ", " Ser ", " Ha ",
    " Para ", " Sus ", " Más ", " Del ", " Es ", " Al ", " Lo ", " Le ", " Les ", " Con ", " Sino ",
    " Son ", " Se ", " Redacción ", " Pero ", " Cual ", " Esto ", " Uno ", " Dos ", " Tres ", " Donde ",
    " Cuatro ", " Cinco ", " Seis ", " Siete ", " Ocho ", " Nueve ", " Diez ", " Cien ", " Mil ", " Sé ",
    " Miles ", " Cientos ", " Millones ", " Tras ", " Pues ", " Vale ", " Entre ", " Contra ", " Me ",
    " Ni "
]


def add_extra_words():
    """Adds the lowercase and uppercase version of all words to COMMON_WORDS."""

    extra_words = list()

    for word in COMMON_WORDS:
        extra_words.append(word.lower())
        extra_words.append(word.upper())

    COMMON_WORDS.extend(extra_words)


add_extra_words()


def get_summary(article, title=""):
    """Generates the top words and sentences from the article text.

    Parameters
    ----------
    article : str
        The article text.

    title : str
        The article title.

    Returns
    -------
    dict
        A dict containing the title of the article, top words and the top scored sentences.

    """

    # Now we prepare the article for scoring.
    cleaned_article = clean_article(article)
    prepared_article = "  " + cleaned_article

    for item in COMMON_WORDS:
        # The white space is used to avoid concatenating words by accident.
        prepared_article = prepared_article.replace(item, " ")

    # We use the Counter class to count all words ocurrences.
    # We then delete the empty string which is often the one with more occurrences.
    scored_words = Counter(prepared_article.split(" "))
    del scored_words[""]

    for word in scored_words:

        # We add bonus points to words starting in uppercase and are equal or longer than 4 characters.
        if word[0].isupper() and len(word) >= 4:
            scored_words[word] *= IMPORTANT_WORDS_MULTIPLIER

        # If the word is a number we punish it by settings its points to 0.
        if word.isdigit():
            scored_words[word] = 0

    top_sentences = get_top_sentences(cleaned_article, scored_words)
    top_sentences_length = sum([len(sentence) for sentence in top_sentences])
    reduction = 100 - (top_sentences_length / len(cleaned_article)) * 100

    summary_dict = {
        "title": title,
        "top_words": get_top_words(scored_words),
        "top_sentences": top_sentences,
        "reduction": reduction
    }

    return summary_dict


def clean_article(article_text):
    """Cleans and reformats the article text.

    Parameters
    ----------
    article_text : str
        The article string.

    Returns
    -------
    str
        The cleaned up article.

    """

    # We divide the script into lines, this is to remove unnecessary whitespaces.
    lines_list = list()

    for line in article_text.split("\n"):

        # We remove whitespaces.
        stripped_line = line.strip()

        # If the line is too short we ignore it.
        if len(stripped_line) >= LINE_LENGTH_THRESHOLD:
            lines_list.append(stripped_line)

    # Now we have the article fully cleaned.
    return "   ".join(lines_list)


def get_top_words(scored_words):
    """Gets the top scored words from the prepared article.

    Parameters
    ----------
    scored_words : dict
        A dict with all the words and their scores.

    Returns
    -------
    list
        An ordered list with the top words.

    """

    # Once we have our words scored it's time to get top ones.
    top_words = list()

    # We convert the sorted_words dict into a list of tuples and then sort it.
    scored_words_sorted = sorted(
        [[score, word] for word, score in scored_words.items()], reverse=True)

    for score, word in scored_words_sorted:

        add_to_list = True

        # We avoid duplicates by checking if the word already is in the top_words list.
        if word.upper() not in [item.upper() for item in top_words]:

            # Sometimes we have the same word but in plural form, we skip the word when that happens.
            for item in top_words:
                if word.upper() in item.upper():
                    add_to_list = False

            if add_to_list:
                top_words.append(word)

    return top_words[0:NUMBER_OF_TOP_WORDS]


def get_top_sentences(cleaned_article, scored_words):
    """Gets the top scored sentences from the cleaned article.

    Parameters
    ----------
    cleaned_article : str
        The original article after it has been cleaned and reformatted.

    scored_words : dict
        A dict with all the words and their scores.

    Returns
    -------
    list
        An ordered list with the top sentences.

    """

    # Now its time to score each sentence.
    scored_sentences = list()

    # We take a reference of the order of the sentences, this will be used later.
    for index, line in enumerate(tokenize.sent_tokenize(cleaned_article)):

        # In some edge cases we have duplicated sentences, we make sure that doesn't happen.
        if line not in [line for score, index, line in scored_sentences]:
            scored_sentences.append(
                [score_line(line, scored_words), index, line])

    top_sentences = list()
    counter = 0

    for score, index, sentence in sorted(scored_sentences, reverse=True):

        if counter >= NUMBER_OF_SENTENCES:
            break

        # When the article is too small the sentences may come empty.
        if len(sentence) >= 3:

            # We clean the sentence and its index so we can sort in chronological order.
            top_sentences.append([index, sentence])
            counter += 1

    return [sentence for index, sentence in sorted(top_sentences)]


def score_line(line, scored_words):
    """Updates the Reddit post with the specified Markdown message.

    Parameters
    ----------
    line : str
        A sentence from the article.

    scored_words : Counter
        A dictionary of all the words from the article with their number of ocurrences.

    Returns
    -------
    int
        The total score of all the words in the sentence.

    """

    temp_line = line[:]

    # We then apply the same clean algorithm. Removing common words.
    for word in COMMON_WORDS:
        temp_line = temp_line.replace(word, " ")

    # We now sum the total number of ocurrences for all words.
    temp_score = 0

    for word in temp_line.split(" "):
        temp_score += scored_words[word]

    return temp_score
