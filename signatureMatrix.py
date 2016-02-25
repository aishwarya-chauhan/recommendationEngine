import mysql.connector
import re
import binascii
import random
import time
import unicodedata
from html.parser import HTMLParser

start_time = time.time()
SHINGLE_LENGTH = 3
HASH_NUMBER = 100
shingleMatrix = {}
postIds = []
maxShingleID = 2**32-1
nextPrime = 4294967311

#Random samples to generate 10 random hash fuctions.
randomSamples = [random.sample(range(maxShingleID), HASH_NUMBER) for i in range(2)]

class HTMLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.fed = []
    def handle_data(self, data):
        self.fed.append(data)
    def get_data(self):
        return ''.join(self.fed)

def getPosts():
    """ To fetch posts from database """
    connection = mysql.connector.connect(user='root', password='', host='localhost', database='posts')
    cursor = connection.cursor()
    cursor.execute("""
        SELECT   id, LOWER(post_content_filtered)
        FROM     wp_posts 
        WHERE    post_status = 'publish'
        AND      post_type = 'normal'
        AND   id in(168506,168610,168625,168637)
    """)
    #168506=medicine,168610=asus router ,168625=z5,168637=z5..
    posts = cursor.fetchall()
    cursor.close()
    return posts

def filterPostContent(data):
    """ To remove tags,multispaces and store simple string of data """
    stripTags = HTMLStripper()
    stripTags.feed(data)
    data = stripTags.get_data()
    data = re.sub('[^\s0-9A-Za-zÀ-ÿ]', ' ', data)
    return(data)

def createShingleMatrix(postId, data):
  """ To create shingles of length SHINGLE_LENGTH """
  data = data.split()
  for i in range(len(data) - SHINGLE_LENGTH + 1):
        shingle = data[i : i + SHINGLE_LENGTH]
        shingle = str(shingle)
        hashedShingle = binascii.crc32(shingle.encode('utf-8')) & 0xfffffff
        if hashedShingle in shingleMatrix:
            shingleMatrix[hashedShingle].append(postId)
        else:
            shingleMatrix[hashedShingle] = [postId]


def hashFunction(shingle, length):
    """ To create a list of HASH_NUMBER hash functions """
    hashValues = []
    for i in range(HASH_NUMBER):
        hashValues.append(((randomSamples[0][i] * shingle + randomSamples[1][i]) % nextPrime)%(nextPrime-1))
    return hashValues

def createSignatureMatrix():  
    signatureMatrix = {postId:[nextPrime+1 for i in range(HASH_NUMBER)] for postId in postIds}
    shingleMatrixLength = len(shingleMatrix)
    for shingle in shingleMatrix:
        hashValues = hashFunction(shingle, shingleMatrixLength)
        for postId in shingleMatrix[shingle]:
            for numHashes in range(HASH_NUMBER):
                if hashValues[numHashes] < signatureMatrix[postId][numHashes]:
                    signatureMatrix[postId][numHashes] = hashValues[numHashes]
    return(signatureMatrix)

posts = getPosts()

for post in posts:
    postContent = filterPostContent(post[1])
    createShingleMatrix(post[0], postContent)
    postIds.append(post[0])

signatureMatrix = createSignatureMatrix()

for i in signatureMatrix:
    print(i," : ", signatureMatrix[i])


keyList=list(signatureMatrix)
max=0
print(" ")
for docid in range(len(keyList)):
    for doid in range(docid+1,len(keyList)):
        count = 0
        for k in range(HASH_NUMBER):
            count = count + (signatureMatrix[keyList[docid]][k] == signatureMatrix[keyList[doid]][k])
        print(keyList[docid]," 's similarity to ",keyList[doid]," count", count)
        if max <= count:
            max=count
            d=docid
            c=doid
print("max count is btw",d+1, " & ", c+1)
print("TIME taken")
print(time.time() - start_time)
    