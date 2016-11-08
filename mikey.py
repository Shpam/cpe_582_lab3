'''
  Miguel Aguilar
  Sam Lakes
  Sage Maxwell
  CPE582-01, Lab 3
'''

import nltk, re, math, random
import numpy as np
import cleanData
from bs4 import BeautifulSoup
from curses.ascii import isdigit
from nltk.corpus import cmudict
d = cmudict.dict()

def url_count(bodies):
  # COUNT THE NUMBER OF URLS IN THE BODY OF THE EMAILS
  urls = re.findall(r'(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?', ' '.join(bodies))
  return len(urls)

def clean_text(text):
  # REMOVES WORDS WITH DIGITS IN THEM
  clean = re.sub(r'\w*\d\w*', '', text).strip()
  clean = re.sub(r'(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?', '', clean)

  #clean = re.sub('<[^>]*>', '', clean)
  soup = BeautifulSoup(clean, 'lxml')
  clean = soup.get_text()

  return clean

def nsyl(word):
  if word.lower() in d:
    return max([len(list(y for y in x if y[-1].isdigit())) for x in d[word.lower()]])
  else:
    return 0

def extract_features(body, raw=False):
  feat = {}
  sentence_tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
  word_tokenizer = nltk.tokenize.RegexpTokenizer(r'\w+')
  clean_body = clean_text(body)

  tokens = nltk.word_tokenize(clean_body.lower())
  words = word_tokenizer.tokenize(clean_body.lower())
  sentences = sentence_tokenizer.tokenize(clean_body)
  vocab = set(words)
  words_per_sentence = np.array([len(word_tokenizer.tokenize(s)) for s in sentences])
  syllables_per_word = sum([nsyl(w) for w in words]) / len(words)

  urls = re.findall(r'(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?', body)

  feat['url_count'] = len(urls)
  feat['avg_words_sent'] = int(math.floor(words_per_sentence.mean()/5))*5
  feat['sent_len_variation'] = int(math.floor(words_per_sentence.std()/5))*5
  feat['lex_diversity'] = round( len(vocab) / float(len(words)), 4)
  feat['avg_sylla_word'] = round(syllables_per_word, 4) # Maybe 2 or 3
  feat['reading_score'] = int( math.floor( (206.835 - (1.015 * words_per_sentence.mean()) - (84.6 * syllables_per_word))/5 ))*5

  if raw:
    return (206.835 - (1.015 * words_per_sentence.mean()) - (84.6 * syllables_per_word))

  return feat

def classify_candidates(candidate_bodies):
  ndx = len(candidate_bodies)//3
  random.shuffle(candidate_bodies)

  feat_label = [(extract_features(tup[0]), tup[1]) for tup in candidate_bodies]

  test_set, train_set = feat_label[:ndx], feat_label[ndx:]

  classifier = nltk.NaiveBayesClassifier.train(train_set)
  #print('ACCURACY: %f'%nltk.classify.accuracy(classifier, test_set))
  return nltk.classify.accuracy(classifier, test_set)


def main():
  #print('Hello World')
  clean_data = cleanData.get_cleaned_data()
  candidates = list(clean_data.keys())
  #print(candidates)
  #print('')

  candidate_bodies = []
  candidate_url_ratios = []
  candidate_vocab_depth = []
  candidate_read_ease = []
  candidate_froms = []
  for candidate in candidates:
    emails = clean_data[candidate]
    #print(candidate)
    #print('TOTAL NUMBER OF EMAILS: %d'%len(emails))

    subjects = []
    bodies = []
    froms = []
    for email in emails:
      subjects.append(email['Subject'])
      bodies.append(email['body'])
      froms.append(email['From'])

      if len(email['body']) > 0:
        candidate_bodies.append((email['body'],candidate))


    # NUMBER OF URLS FOUND IN EMAILS
    num_urls = url_count(bodies)
    #print('URL COUNT: %d'%num_urls)
    #print('URL TO EMAIL RATIO: %f'%(num_urls/len(emails)))
    candidate_url_ratios.append((candidate, num_urls/len(emails)))

    # NUMBER OF UNIQUE FORWARDING EMAIL ADDRESSES
    #print('UNIQUE FROMS:')
    #print(set(froms))
    #print('UNIQUE FROMS: %d'%(len(set(froms))))
    candidate_froms.append((candidate,len(set(froms))))

    score = extract_features(' '.join(bodies), True)
    candidate_read_ease.append((candidate, score))


    # MAYBE CHANGE THE ORDERING, TOKENIZE THE WORDS AND THEN REMOVE THE WEIRD INSTANCES
    subjects = clean_text(' '.join(subjects))
    bodies = clean_text(' '.join(bodies))

    subject_tokens = nltk.tokenize.RegexpTokenizer(r'\w+').tokenize(subjects)
    subject_words = [word.lower() for word in subject_tokens if word not in nltk.corpus.stopwords.words('english')]
    subject_freq = nltk.FreqDist(subject_words)
    #print('SUBJECT FREQ WORDS:')
    #print(subject_freq.most_common(50))


    body_tokens = nltk.tokenize.RegexpTokenizer(r'\w+').tokenize(bodies)
    body_words = [word.lower() for word in body_tokens if word not in nltk.corpus.stopwords.words('english')]
    body_freq = nltk.FreqDist(body_words)
    #print('BODY FREQ WORDS:')
    #print(body_freq.most_common(50))


    #print('UNIQUE WORDS: %d'%len(set(body_words)))
    #print('TOTAL WORDS: %d'%len(body_words))
    #print('VOCABULARY DEPTH: %f'%( math.log10(len(set(body_words)))/math.log10(len(body_words)) ))
    candidate_vocab_depth.append((candidate, math.log10(len(set(body_words)))/math.log10(len(body_words))))

    #exit(1)


  print('UNIQUE FROMS:')
  sorted_froms = sorted(candidate_froms, key=lambda x: x[1])
  print(sorted_froms)
  print('')

  print('URL RATIOS:')
  sorted_url = sorted(candidate_url_ratios, key=lambda x: x[1])
  print(sorted_url)
  print('')

  print('VOCAB DEPTH:')
  sorted_vocab = sorted(candidate_vocab_depth, key=lambda x: x[1])
  print(sorted_vocab)
  print('')


  '''
  The Flesch Reading Ease Score:
    90-100 : Very Easy 
    80-89  : Easy 
    70-79  : Fairly Easy 
    60-69  : Standard 
    50-59  : Fairly Difficult 
    30-49  : Difficult 
    0-29   : Very Confusing 
  '''
  print('READING EASE SCORE:')
  sorted_read = sorted(candidate_read_ease, key=lambda x: x[1], reverse=True)
  print(sorted_read)
  print('')

  acc_sum = 0.0
  for i in range(5):
    acc_sum += classify_candidates(candidate_bodies)
  print('AVERAGE ACCURACY: %f'%(acc_sum/5))
  print('')

if __name__ == '__main__':
  main()