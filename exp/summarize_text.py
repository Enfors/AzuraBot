#!/usr/bin/env python
# Based on https://st-ackabuse.com/text-summarization-with-nltk-in-python/

import bs4 as bs
import re
import urllib.request

import nltk

scraped_data = urllib.request.urlopen(
#    "https://sv.wikipedia.org/wiki/Anders_Pettersson_(kampsportare)")
#    "https://sv.wikipedia.org/wiki/Drakar_och_Demoner")
#    "https://sv.wikipedia.org/wiki/Target_Games")
    "https://sv.wikipedia.org/wiki/Moralpanik")
article = scraped_data.read()

parsed_article = bs.BeautifulSoup(article, "lxml")

paragraphs = parsed_article.find_all("p")

article_text = ""

for p in paragraphs:
    article_text += p.text + " "

# article_text = """This is the first sentence, which is rather boring.
# The second is also boring, don't you think?
# The third one is a bit longer and has more words, so perhaps it has some value?
# The fourth, however, does not.
# And the fifth one is also rather bland.
# When it comes to the sixth sentence, nobody cares.
# Now I am to privde something more thrilling when it comes to number seven, I wonder if this will work.
# """

# Remove Square Brackeds and extra spaces
article_text = re.sub(r'\[[0-9]*\]', ' ', article_text)
article_text = re.sub(r'\s+', ' ', article_text)

# Remove special characters and digits
# formatted_article_text = re.sub('[^a-öA-Ö]', '', article_text)
# formatted_article_text = re.sub(r'\s+', ' ', formatted_article_text)
formatted_article_text = re.sub(r'\s+', ' ', article_text)

sentence_list = nltk.sent_tokenize(article_text)
summary = sentence_list[0] + " "
sentence_list = sentence_list[1:]
num_sentences = len(sentence_list)
print(f"Number of sentences: {num_sentences}")
stopwords = nltk.corpus.stopwords.words("swedish")

word_frequencies = {}
for word in nltk.word_tokenize(formatted_article_text):
    if word not in stopwords:
        if word not in word_frequencies.keys():
            word_frequencies[word] = 1
        else:
            word_frequencies[word] += 1

maximum_frequency = max(word_frequencies.values())

for word in word_frequencies.keys():
    word_frequencies[word] = word_frequencies[word] / maximum_frequency

sentence_scores = {}

for sent in sentence_list:
    for word in nltk.word_tokenize(sent.lower()):
        if word in word_frequencies.keys():
            if len(sent.split(" ")) < 30:
                if sent not in sentence_scores.keys():
                    sentence_scores[sent] = word_frequencies[word]
                else:
                    sentence_scores[sent] += word_frequencies[word]

num_sum_sentences = 0

sorted_scores = sorted(sentence_scores.values(), reverse=True)
cutoff_index = int(len(sorted_scores) * 0.3 + 0.5)

print(f"Cutoff index: {cutoff_index}")
cutoff_value = sorted_scores[cutoff_index]
print(f"Cutoff value: {cutoff_value:.3f}")

# for num, score in enumerate(sorted_scores):
#     print(f"{num:3d}: {score:0.3f}", end="")
#     if score < cutoff_value:
#         print("-")
#     else:
#         print("+")

for sent in sentence_scores.keys():
    score = sentence_scores[sent]
    if score < cutoff_value:
        print("- ", end="")
    else:
        print("+ ", end="")
        summary += sent + " "
        num_sum_sentences += 1

    print(f"{sentence_scores[sent]:.3f}: {sent}")

print("==================")

print(f"Sentences: {num_sentences}, in summary: {num_sum_sentences}")

print(summary)
