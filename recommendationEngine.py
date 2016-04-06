import mysql.connector
import re
import binascii
import random
import time
from html.parser import HTMLParser

random.seed(10)
start_time = time.time()
SHINGLE_LENGTH = 3
HASH_NUMBER = 99
BANDS = 33
ROWS = 3
NEXT_PRIME = 4294967311
MAX_SHINGLE_ID = 2**32 - 1
BAND_RANGE = range(BANDS)
HASH_NUMBER_RANGE = range(HASH_NUMBER)
randomSamples = [random.sample(range(MAX_SHINGLE_ID), HASH_NUMBER) for i in range(2)]
postIds = []
shingleMatrix = {}
recommendations = {}

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
        ORDER BY Id DESC LIMIT 1000
        """)
    posts = cursor.fetchall()
    cursor.close()
    return posts

def filterPostContent(data):
    """ To remove tags,multispaces and store simple string of data """
    stripTags = HTMLStripper()
    stripTags.feed(data)
    data = stripTags.get_data()
    data = re.sub('[^\s0-9A-Za-zÀ-ÿ]', ' ', data)
    return data

def createShingleMatrix(shingleMatrix ,postId, data):
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
  return shingleMatrix

def hashFunction(shingle):
    """ To create a list of HASH_NUMBER hash functions """
    hashValues = []
    for index in HASH_NUMBER_RANGE:
        hashValues.append(((randomSamples[0][index] * shingle + randomSamples[1][index]) % NEXT_PRIME) % (NEXT_PRIME - 1))
    return hashValues

def createSignatureMatrix(postIds, shingleMatrix):
    """ To generate MinHash Signatures """
    signatureMatrix = {postId:[NEXT_PRIME + 1 for index in HASH_NUMBER_RANGE] for postId in postIds}
    for shingle in shingleMatrix:
        hashValues = hashFunction(shingle)
        for postId in shingleMatrix[shingle]:
            for numHashes in HASH_NUMBER_RANGE:
                if hashValues[numHashes] < signatureMatrix[postId][numHashes]:
                    signatureMatrix[postId][numHashes] = hashValues[numHashes]
    return signatureMatrix

def getRecommendedPosts(signatureMatrix):
    """ To get list of candidate pairs in hash buckets """
    for band in BAND_RANGE:
        bandCandidates = {}
        for postId in signatureMatrix:
            postValue = []
            for hashIndex in range(band * ROWS, ROWS * (band + 1)):
                postValue.append(signatureMatrix[postId][hashIndex])
            hashValue = binascii.crc32((",".join(map(str, postValue))).encode('utf-8')) & 0xfffffff
            if hashValue in bandCandidates and postId not in bandCandidates[hashValue]:
                bandCandidates[hashValue].append(postId)
            else:
                bandCandidates[hashValue] = [postId]
        for hashValue in bandCandidates:
            for index in range(len(bandCandidates[hashValue])):
                if bandCandidates[hashValue][index] not in recommendations:
                    recommendations[bandCandidates[hashValue][index]] = bandCandidates[hashValue][:index] + bandCandidates[hashValue][index + 1:]
                else:
                    recommendations[bandCandidates[hashValue][index]] += bandCandidates[hashValue][:index] + bandCandidates[hashValue][index + 1:]
    for key in recommendations:
        recommendations[key] = list(set(recommendations[key]))
    return recommendations

def insertRecommendedPosts(recommendations):
    """ To insert recommended postIds in the database """
    connection = mysql.connector.connect(user='root', password='', host='localhost', database='posts')
    cursor = connection.cursor()
    cursor.execute(""" TRUNCATE TABLE candidates """)
    for key in recommendations:
        if len(recommendations[key]) >= 1:
            similarPostId = ','.join(str(postId) for postId in recommendations[key])
            format_str = """
                          INSERT IGNORE INTO candidates(postId, similarPostIds) 
                          VALUES('{postId}', '{similarPostId}')
                        """
            sql_command = format_str.format(postId = key, similarPostId = similarPostId)
            cursor.execute(sql_command)
    connection.commit()
    cursor.close()

if __name__ == '__main__':
    posts = getPosts()

    for post in posts:
        postContent = filterPostContent(post[1])
        createShingleMatrix(shingleMatrix, post[0], postContent)
        postIds.append(post[0])

    signatureMatrix = createSignatureMatrix(postIds, shingleMatrix)
    del shingleMatrix

    recommendations = getRecommendedPosts(signatureMatrix)
    del signatureMatrix
    
    insertRecommendedPosts(recommendations)

    print("TIME taken")
    print(time.time() - start_time)