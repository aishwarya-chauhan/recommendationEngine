import unittest
import recommendationEngine as mining

class mytest(unittest.TestCase):
    
    def setUp(self):
        self.postId = 1
        self.data = "hey what you doing"
        self.shingleMatrix = {10:[1],12:[1,2],13:[2],14:[1,2]}
        self.randomSamples = [[1,2,3,4],[3,4,2,1]]
        self.postIds = [1,2]
        self.NEXT_PRIME = 10
        self.HASH_NUMBER = 4
        self.BANDS=2
        self.ROWS=2
        self.BAND_RANGE = range(self.BANDS)
        self.HASH_NUMBER_RANGE = range(self.HASH_NUMBER)
        self.signatureMatrixTest = {1: [3, 2, 2, 0], 2: [5, 0, 2, 0], 3:[3,2,5,0], 4:[5,0,4,2]}
        
    def testFilterPostContent(self):
        dataInput = "<p>Sony aprovechará para que.. sea la base de la gestión de perfiles de usuarios, \nlo que</p>"
        dataOutput = "Sony aprovechará para que   sea la base de la gestión de perfiles de usuarios  \nlo que"
        self.assertEqual(mining.filterPostContent(dataInput), dataOutput)

    def testCreateShingleMatrix(self):
        mining.shingleMatrix = {}
        dataOutput = mining.createShingleMatrix(mining.shingleMatrix, self.postId, self.data)
        print(dataOutput)
    
    def testHashFunction(self):
        dataInput = 10
        dataOutput = [3,4,2,1]
        mining.randomSamples = self.randomSamples
        mining.HASH_NUMBER = self.HASH_NUMBER
        mining.NEXT_PRIME = self.NEXT_PRIME
        mining.HASH_NUMBER_RANGE = self.HASH_NUMBER_RANGE
        self.assertEqual(mining.hashFunction(dataInput), dataOutput)
   
    def testCreateSignatreMatrix(self):
        mining.randomSamples = self.randomSamples
        mining.HASH_NUMBER = self.HASH_NUMBER
        mining.NEXT_PRIME = self.NEXT_PRIME
        mining.HASH_NUMBER_RANGE = self.HASH_NUMBER_RANGE
        dataOutput = mining.createSignatureMatrix(self.postIds, self.shingleMatrix)
        print(dataOutput)

    def testGetRecommendedPosts(self):
        mining.BANDS = self.BANDS 
        mining.ROWS =  self.ROWS
        mining.BAND_RANGE = self.BAND_RANGE
        dataOutput = {1: [2, 3], 2: [1, 4], 3: [1], 4: [2]}
        self.assertEqual(mining.getRecommendedPosts(self.signatureMatrixTest), dataOutput)

if __name__ == '__main__':
    unittest.main()