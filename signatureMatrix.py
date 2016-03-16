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
BANDS = 20 
ROWS = 5
postIds = []
shingleMatrix = {}
candidatePairs = {}
recommendations = {}
maxShingleID = 2**32 - 1
randomSamples = [random.sample(range(maxShingleID), HASH_NUMBER) for i in range(2)]
nextPrime = 4294967311

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
    return(data)

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
  return(shingleMatrix)
 
def hashFunction(shingle, randomSamples, HASH_NUMBER, nextPrime):
    """ To create a list of HASH_NUMBER hash functions """
    hashValues = []
    for index in range(HASH_NUMBER):
        hashValues.append(((randomSamples[0][index] * shingle + randomSamples[1][index]) % nextPrime) % (nextPrime - 1))
    return hashValues

def createSignatureMatrix(postIds, shingleMatrix, randomSamples, HASH_NUMBER, nextPrime):
    """ To generate MinHash Signatures """
    signatureMatrix = {postId:[nextPrime + 1 for index in range(HASH_NUMBER)] for postId in postIds}
    for shingle in shingleMatrix:
        hashValues = hashFunction(shingle,randomSamples, HASH_NUMBER, nextPrime)
        for postId in shingleMatrix[shingle]:
            for numHashes in range(HASH_NUMBER):
                if hashValues[numHashes] < signatureMatrix[postId][numHashes]:
                    signatureMatrix[postId][numHashes] = hashValues[numHashes]
    return(signatureMatrix)

def getCandidatePairs(signatureMatrix, BANDS, ROWS):
    """ To get list of candidate pairs in hash buckets """
    for band in range(BANDS):
        for docid in signatureMatrix:
            rowValue = []
            for hashIndex in range(band * ROWS, ROWS * (band + 1)):
                rowValue.append(signatureMatrix[docid][hashIndex])
            hashValue = binascii.crc32((",".join(map(str, rowValue))).encode('utf-8')) & 0xfffffff
            if hashValue in candidatePairs and docid not in candidatePairs[hashValue]:
                candidatePairs[hashValue].append(docid)
            else:
                candidatePairs[hashValue] = [docid]
    return(candidatePairs)

def insertSimilarPosts(candidatePairs):
    """ To insert recommended postIds in the database """
    connection = mysql.connector.connect(user='root', password='', host='localhost', database='posts')
    cursor = connection.cursor()
    for candidate in candidatePairs:
        if len(candidatePairs[candidate]) > 1:
            for index, postId in enumerate(candidatePairs[candidate]):
                if postId in recommendations:
                    recommendations[postId] += candidatePairs[candidate][:index] + candidatePairs[candidate][index + 1:]
                else:
                    recommendations[postId] = candidatePairs[candidate][:index] + candidatePairs[candidate][index + 1:]
    cursor.execute(""" TRUNCATE TABLE candidates """)
    for key in recommendations:
        recommendations[key] = list(set(recommendations[key]))
        similarPostId = ','.join(str(postId) for postId in recommendations[key])
        format_str = """
                      INSERT IGNORE INTO candidates(postId, similarPostIds) 
                      VALUES('{postId}', '{similarPostId}')
                    """
        sql_command = format_str.format(postId = key, similarPostId = similarPostId)
        cursor.execute(sql_command)
    print("recommendations: ",recommendations)
    connection.commit()
    cursor.close()

def jacaardSimilarity(posts):
    """ To calculate jaccard similarity of all candidate pairs """
    jaccard_dict = {}
    for post in posts:
        data = filterPostContent(post[1])
        data = data.split()
        for i in range(len(data) - SHINGLE_LENGTH + 1):
            shingle = data[i : i + SHINGLE_LENGTH]
            shingle = str(shingle)
            jaccard_dict.setdefault(post[0],[]).append(shingle)  
    for key in jaccard_dict:
        for keynext in jaccard_dict:
            if keynext != key:
                common = set(jaccard_dict[key]).intersection( set(jaccard_dict[keynext]))
                a = len(common) / (len(jaccard_dict[key]) + len(jaccard_dict[keynext]))
                print( key , " & ", keynext, " = ", a)
    
if __name__ == '__main__':
    posts = getPosts()

    #jacaardSimilarity(posts)
    
    for post in posts:
        postContent = filterPostContent(post[1])
        createShingleMatrix(shingleMatrix, post[0], postContent)
        postIds.append(post[0])
    
    signatureMatrix = createSignatureMatrix(postIds, shingleMatrix, randomSamples, HASH_NUMBER, nextPrime)
    del shingleMatrix
    candidatePairs = getCandidatePairs(signatureMatrix, BANDS, ROWS)
    del signatureMatrix
    insertSimilarPosts(candidatePairs)
    
    print("TIME taken")
    print(time.time() - start_time)