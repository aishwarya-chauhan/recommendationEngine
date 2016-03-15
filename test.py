import unittest
import unittest.mock
import signatureMatrix as mining

class mytest(unittest.TestCase):
    
    def setUp(self):
        self.shingleMatrixTest = {}
        self.postId = 1
        self.data = "hey what you doin"
        self.shingleMatrix = {10:[1],12:[1,2],13:[2],14:[1,2]}
        self.randomSamples = [[1,2,3,4],[3,4,2,1]]
        self.postIds = [1,2]
        self.nextPrime = 10
        self.HASH_NUMBER = 4
        self.BANDS=2
        self.ROWS=2
        self.signatureMatrixTest = {1: [3, 2, 2, 0], 2: [5, 0, 1, 0]}
        
    def testFilterPostContent(self):
        dataInput = "<p>Sony aprovechará para que.. sea la base de la gestión de perfiles de usuarios, \nlo que</p>"
        dataOutput = "Sony aprovechará para que   sea la base de la gestión de perfiles de usuarios  \nlo que"
        self.assertEqual(mining.filterPostContent(dataInput), dataOutput)

    def testCreateShingleMatrix(self):
        dataOutput = mining.createShingleMatrix(self.shingleMatrixTest, self.postId, self.data)
        print(dataOutput)
    
    def testHashFunction(self):
        dataInput = 10
        dataOutput = [3,4,2,1]
        self.assertEqual(mining.hashFunction(dataInput,self.randomSamples, self.HASH_NUMBER, self.nextPrime), dataOutput)
   
    def testCreateSignatreMatrix(self):
        dataOutput = mining.createSignatureMatrix(self.postIds, self.shingleMatrix, self.randomSamples, self.HASH_NUMBER, self.nextPrime)
        print(dataOutput)

    def testGetCandidatePairs(self):
        dataOutput = mining.getCandidatePairs(self.signatureMatrixTest, self.BANDS, self.ROWS)
        print(dataOutput)

if __name__ == '__main__':
    unittest.main()