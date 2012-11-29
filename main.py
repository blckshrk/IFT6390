#! /usr/bin/env python2
# -*- coding: utf-8 -*-
###################################
#
# Reconnaissance par "Eigenfaces"
#
###################################
from eigenfaces import Eigenfaces
import tools
import sys

## MAIN ###########################

# Parametres du script
K = 1
Theta = 0.5
trainFile = "./Databases/train1.txt"
testFile = "./Databases/test4.txt"

if(len(sys.argv) > 1 and sys.argv[1] == "-h"):
    print "Usage: main.py [OPTION]"
    print "Options: \n\
          -h\t\tPrint this message\n\
          -k\t\tThe number of neighbors (default: 1)\n\
          -theta\tThe gaussian kernel size (default: 0.5)\n\
          -train\tThe train file\n\
          -test\t\tThe test file\n"

    sys.exit()

if( len(sys.argv) > 2 ):
	for i in range(1, len(sys.argv), 2):
		if(sys.argv[i] == "-k"):
		    K = int( sys.argv[i+1] )
		
		elif(sys.argv[i] == "-theta"):
			Theta = float( sys.argv[i+1] )

		elif(sys.argv[i] == "-train"):
			trainFile = sys.argv[i+1]

		elif(sys.argv[i] == "-test"):
			testFile = sys.argv[i+1]


# Chargement des données
dataTrain, dataTrainIndices = tools.loadImageData( trainFile )

# eigen model
eigen_model = Eigenfaces(Theta, K)
eigen_model.train(dataTrain, dataTrainIndices)

## TEST ###########################
dataTest, dataTestIndices = tools.loadImageData( testFile )

nbGoodResult = 0
nbGoodResult2 = 0 # compteurs de bons résultats
nbGoodResult3 = 0

#x = np.array(range(0, 100))
#y = gaussianKernel( 50, x, theta=Theta )
#print y

#pylab.plot(x, y)
#pylab.show()
#storeData()
#loadData()

for i in range(0, int( dataTest.shape[1] )):

	iDataTrain = eigen_model.compute_predictions( dataTest[:,i] )
	if(dataTrainIndices[iDataTrain] == dataTestIndices[i]):
		nbGoodResult += 1
	
	resultKNN = eigen_model.compute_predictions( dataTest[:,i], "knn" )
	if(resultKNN == dataTestIndices[i]):
	    nbGoodResult2 += 1

	resultParzen = eigen_model.compute_predictions( dataTest[:,i], "parzen" )
	if(resultParzen == dataTestIndices[i]):
		nbGoodResult3 += 1
	
	print "Classic method: "+ str( dataTrainIndices[iDataTrain] ) +" | KNN method: "+ str( resultKNN ) +" | KNN+Parzen method: "+ str( resultParzen ) +" | Expected: "+ str( dataTestIndices[i] ) +"\n" # +1 car l'index de la matrice commence a 0

print "Accuracy with classic method: "+ str( (nbGoodResult / float(dataTest.shape[1])) * 100 ) +"%"
print "Accuracy with KNN method (k="+ str(K) +"): "+ str( (nbGoodResult2 / float(dataTest.shape[1])) * 100 ) +"%"
print "Accuracy with KNN + Parzn window method (k="+ str(K) +" theta="+ str(Theta) +"): "+ str( (nbGoodResult3 / float(dataTest.shape[1])) * 100 ) +"%"


