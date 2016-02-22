import mysql.connector
import re
import binascii
import random
import time
import unicodedata
from bs4 import BeautifulSoup

start_time = time.time()
SHINGLE_LENGTH = 9
hashNumber = 100
shingleMatrix = {}
postIds = []

#Random samples to generate 10 random hash fuctions.
randomSamples = [random.sample(range(10000), hashNumber) for i in range(2)]

def stripAccents(data):
    """ To convert accent words to normal letters """
    data = unicodedata.normalize('NFD', data)
    data = data.encode('ascii', 'ignore')
    data = data.decode("utf-8")
    return str(data)

def filterPostContent(data):
    """ To remove tags,multispaces and store simple string of data """
    data = BeautifulSoup(data, 'html.parser').get_text()
    data = stripAccents(data.lower())
    data = re.sub('[^0-9a-zA-Z]', '', data)
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
    for i in range(hashNumber):
        hashValues.append((randomSamples[0][i] * shingle + randomSamples[1][i]) % length)
    return hashValues

def createSignatureMatrix():  
    signatureMatrix = {postId:[42345600 for i in range(hashNumber)] for postId in postIds}
    shingleMatrixLength = len(shingleMatrix)
    for shingle in shingleMatrix:
        hashValues = hashFunction(shingle, shingleMatrixLength)
        for postId in shingleMatrix[shingle]:
            for numHashes in range(hashNumber):
                if hashValues[numHashes] < signatureMatrix[postId][numHashes]:
                    signatureMatrix[postId][numHashes] = hashValues[numHashes]
    return(signatureMatrix)

def getPosts():
    connection = mysql.connector.connect(user='root', password='', host='localhost', database='posts')
    cursor = connection.cursor()
    cursor.execute("""
        SELECT   id, post_content_filtered
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
    postContent = filterPostContent(post[1])
    createShingle(post[0], postContent)
    postIds.append(post[0])

signatureMatrix = createSignatureMatrix()

print("TIME taken")
print(time.time() - start_time)