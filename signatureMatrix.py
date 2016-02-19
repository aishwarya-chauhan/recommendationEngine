import mysql.connector
import re
import binascii
import random
import time
import unicodedata
from html.parser import HTMLParser

start_time = time.time()
SHINGLE_LENGTH = 9
HASH_NUMBER = 100
shingleMatrix = {}
postIds = []

#Random samples to generate 10 random hash fuctions.
randomSamples = [random.sample(range(10000), HASH_NUMBER) for i in range(2)]

class HTMLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def filterPostContent(data):
    """ To remove tags,multispaces and store simple string of data """
    stripTags = HTMLStripper()
    stripTags.feed(data)
    data = stripTags.get_data()
    data = re.sub('[^\s0-9A-Za-zÀ-ÿ]|\s{2,}|\n', '', data)
    return(data)

def createShingle(postId, data):
  """ To create shingles of length SHINGLE_LENGTH """
  for i in range(len(data) - SHINGLE_LENGTH - 1):
    shingle = data[i : i + SHINGLE_LENGTH]
    hashedShingle = binascii.crc32(shingle.encode('utf-8')) & 0xfffffff
    if hashedShingle in shingleMatrix:
      shingleMatrix[hashedShingle].append(postId)
    else:
      shingleMatrix[hashedShingle] = [postId]


def hashFunction(shingle, length):
    hashValues = []
    for i in range(HASH_NUMBER):
        hashValues.append((randomSamples[0][i] * shingle + randomSamples[1][i]) % length)
    return hashValues

def createSignatureMatrix():  
    signatureMatrix = {postId:[42345600 for i in range(HASH_NUMBER)] for postId in postIds}
    shingleMatrixLength = len(shingleMatrix)
    for shingle in shingleMatrix:
        hashValues = hashFunction(shingle, shingleMatrixLength)
        for postId in shingleMatrix[shingle]:
            for numHashes in range(HASH_NUMBER):
                if hashValues[numHashes] < signatureMatrix[postId][numHashes]:
                    signatureMatrix[postId][numHashes] = hashValues[numHashes]
    return(signatureMatrix)

def getPosts():
    connection = mysql.connector.connect(user='root', password='', host='localhost', database='posts')
    cursor = connection.cursor()
    cursor.execute("""
        SELECT   id, LOWER(post_content_filtered)
        FROM     wp_posts 
        WHERE    post_status = 'publish'
        AND      post_type = 'normal'
        ORDER BY Id desc LIMIT 1000
    """)
    posts = cursor.fetchall()
    cursor.close()
    return posts

posts = getPosts()


for post in posts:
    postContent = filterPostContent(post[1]
    createShingle(post[0], postContent)
    postIds.append(post[0])

signatureMatrix = createSignatureMatrix()

print("TIME taken")
print(time.time() - start_time)