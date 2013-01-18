#! /usr/bin/env python2
# -*- coding: utf-8 -*-
###################################
#
# Reconnaissance par "Eigenfaces"
#
###################################
import tools
import sys, os
import logging as log
import numpy as np

from pca import PCA
from knn import KNN
from parzen import ParzenWindows
from nnet import NeuralNetwork

#### DEBUT CLASSE MAIN ####################################
class Main (object):

    def __init__(self, K=1, Theta=0.5, 
                 batch_size=1, n_epoch=100, n_hidden=10, lr=0.001, wd=0.,
                 trainFile="", testFile="", debug_mode=True, categorie="ORL", nbExemples=5, stock=0, curv=0, pourcentageTrain=0.6, validation=True):
        # KNN
        self.K = K

        # Parzen
        self.Theta = Theta
        
        # NNET
        self.batch_size = batch_size
        self.n_epoch = n_epoch
        self.n_hidden = n_hidden
        self.lr = lr
        self.wd = wd

        # validation
        self.validation = validation
        
        # categorie  ("LFW", "ORL", "BOTH"), nbExemples
        self.categorie = categorie
        self.nbExemples = nbExemples
        if self.categorie not in ["LFW", "ORL"]:
            log.error("La  categorie d'images étudiees doit être LFW ou ORL")
        if self.nbExemples < 4:
             log.error("Le nombre d'exemples envisages doit >= 4")
        #if self.nbExemples>=400 and self.categorie=="LFW":
            #log.error("Le nombre d'entrees de l'ensemble d'entrainement doit etre constitue de moins de 400 exemples par classes pour le domaine LFW")
        if self.nbExemples > 10 and self.categorie == "ORL":
            log.error("Le nombre d'entrees pour l'etude doit etre constitue de moins de 10 exemples par classes pour le domaine ORL")
        self.pourcentageTrain = pourcentageTrain
        if self.pourcentageTrain >= 1.0 or self.pourcentageTrain <= 0 :
            log.error("Le pourcentage doit etre dans ]0;1[")

        # stock & courbes
        self.stock = stock
        if self.stock not in [0,1]:
            self.stock = 0
        self.curv = curv
        if self.curv not in [0,1]:
            self.curv = 0

        # logger pour debbug
        if debug_mode:
            log.basicConfig(stream=sys.stderr, level=log.DEBUG)
        else:
            log.basicConfig(stream=sys.stderr, level=log.INFO)
    
    #TODO trouver un nom plus subtile..?
    def main(self, algo="KNN", textview=None):
        
        # Remplace "print"
        def print_output(text):
            if textview != None:
                buf = textview.get_buffer()
                buf.insert_at_cursor(text + "\n")
                textview.scroll_mark_onscreen(buf.get_insert())
            else:
                log.info(text)
        
        
        # liste des types de set
        if self.validation == 1:
            listeTypesSet = ["train", "validation", "test"]
        else:
            listeTypesSet = ["train", "test"]

        # liste des resultats utilises pour les courbes
        listeRes=[]

        # creation des trainFile et testFile
        log.debug("Construction des fichiers d'entrainement")
        tools.constructLfwNamesCurrent( self.nbExemples )   

        #TODO ca ne sert plus a rien finalement
        ( nbClassesLFW, nbClassesORL ) = tools.trainAndTestConstruction( self.pourcentageTrain, self.nbExemples )

        # Chargement des données
        dataTrain, dataTrainIndices, nClass = tools.loadImageData( "train", self.categorie)
        
        # tranformation pca
        print_output("Calcul des vecteurs propres...")
        pca_model = PCA( dataTrain )
        pca_model.transform() # on transforme les donné dans un le "eigen space"

        ##### Recherche pas KNN
        if algo == "KNN":
            print_output("Début de l'algorithme des K plus proches voisins...")
            
            # On build le model pour recherche par KNN
            knn_model = KNN( pca_model.getWeightsVectors(), dataTrainIndices, nClass, self.K )
            
            # On build le model pour Parzen
            parzen_model = ParzenWindows( pca_model.getWeightsVectors(), dataTrainIndices, nClass, self.Theta )

            ## TEST ###########################
            #TODO Toute cette partie est a revoir pour sortir des graphes
            # de train, validation, test
            for trainTest in listeTypesSet:
                if trainTest == "train":
                    dataTest, dataTestIndices = dataTrain, dataTrainIndices
                else :
                    ### si l'on n'effectue pas de validation on concatene les entrees de test et de validation initiales pour obtenir le test
                    #if "validation" not in listeTypesSet:
                        #dataTestInitial, dataTestInitialIndices, nClass = tools.loadImageData( "test", self.categorie )
                        #dataValidation, dataValidationIndices, nClass = tools.loadImageData( "validation", self.categorie )
                        #dataTest = np.zeros(dataTestInitial.size + dataValidation.size)
                        #dataTestIndices = np.zeros( dataTest.size )
                        #dataTest[ : dataTestInitial.size], dataTestIndices[ : dataTestInitial.size] = dataTestInitial, dataTestInitialIndices
                        #dataTest[dataTestInitial.size : ], dataTestIndices[dataTestInitial.size : ] = dataValidation, dataValidationIndices
                        
                        
                    #else:
                        dataTest, dataTestIndices, nClass = tools.loadImageData( trainTest, self.categorie )
                

            	# compteurs de bons résultats   
                nbGoodResult = 0
                nbGoodResult2 = 0 
                nbGoodResult3 = 0

                for i in range(0, int( dataTest.shape[1] )):
                	#TODO faire ne projection matriciel
                    proj = pca_model.getProjection( dataTest[:,i] )

		            # k = 1, pour réference
		            # on force k
                    knn_model.setK( 1 )
                    result1NN = knn_model.compute_predictions( proj )
                    if(result1NN == dataTestIndices[i]):
                        nbGoodResult += 1

		            # k = n
		            # replace k a ca position initial
                    knn_model.setK( self.K )
                    resultKNN = knn_model.compute_predictions( proj )
                    if(resultKNN == dataTestIndices[i]):
                        nbGoodResult2 += 1

                
                    resultParzen = parzen_model.compute_predictions( proj )
                    if(resultParzen == dataTestIndices[i]):
                        nbGoodResult3 += 1

                    out_str = "Classic method: "+ str( result1NN ) +" | KNN method: "+ str( resultKNN ) +" | KNN+Parzen method: "+ str( resultParzen ) +" | Expected: "+ str( dataTestIndices[i] ) +"\n" # +1 car l'index de la matrice commence a 0
                    print_output(out_str)

                resClassic = (float(nbGoodResult) / float(dataTest.shape[1])) * 100.
                out_str = "\nAccuracy with classic method: %.3f" % resClassic + "%\n"
                resKNN = (nbGoodResult2 / float(dataTest.shape[1])) * 100.
                out_str += "Accuracy with KNN method (k="+ str( self.K ) +"): %.3f" % resKNN + "%\n"
                res = (nbGoodResult3 / float(dataTest.shape[1])) * 100.
                out_str += "Accuracy with KNN + Parzen window method (theta="+ str( self.Theta ) +"): %.3f" % res + "%\n"
                print_output(out_str)
            
            #### recupere les valeurs finale de l'accuracy
                listeRes.append( 100 - resClassic )
                listeRes.append( 100 - resKNN )
                listeRes.append( 100 - res )
            
        
        #### Recherche pas NNET
        elif algo == "NNET":
			print_output("Début de l'algorithme du Perceptron multicouche...")
			
			# parametre, donnees, etc...
			dataTrain = pca_model.getWeightsVectors()
			dataTrainTargets = (dataTrainIndices - 1).reshape(dataTrainIndices.shape[0], -1)
			#! contrairement au KNN le NNET prends les vecteurs de features en ligne et non pas en colonne
			train_set = np.concatenate((dataTrain.T, dataTrainTargets), axis=1)

			# On build et on entraine le model pour recherche par KNN
			nnet_model = NeuralNetwork( dataTrain.shape[0], self.n_hidden, nClass, self.lr, self.wd )
			nnet_model.train( train_set, self.n_epoch, self.batch_size )

			## TEST ###########################
			#TODO Toute cette partie est a revoir pour sortir des graphes
			# de train, validation, test
			dataTest, dataTestIndices, nClass = tools.loadImageData( "test", self.categorie )
			# compteurs de bons résultats   
			nbGoodResult = 0

			for i in range(0, int( dataTest.shape[1] )):
				#TODO faire ne projection matriciel
				proj = pca_model.getProjection( dataTest[:,i] )
				proj = proj.reshape(1, proj.shape[0])

				#
				resultNNET = np.argmax(nnet_model.compute_predictions( proj ), axis=1)[0] + 1
				if(resultNNET == dataTestIndices[i]):
					nbGoodResult += 1
				out_str = "Result: "+ str( resultNNET ) + " | Expected: "+ str( dataTestIndices[i] ) +"\n" # +1 car l'index de la matrice commence a 0
				print_output(out_str)

			res = (float(nbGoodResult) / float(dataTest.shape[1])) * 100.
			out_str = "\nAccuracy : %.3f" % res + "%\n"
			print_output(out_str)
        return listeRes

#### FIN CLASSE MAIN ####################################

# Si le script est appelé directement on execute ce code
if __name__ == "__main__":
    import argparse

    # Options du script
    parser = argparse.ArgumentParser(description='Facial recognition')
    
    parser.set_defaults(verbose=True)
    parser.add_argument("-v", "--verbose", action="store_true", dest="verbose", help="print status messages to stdout")
    parser.add_argument("-q", "--quiet", action="store_false", dest="verbose", help="don't print status messages to stdout")

    parser.add_argument("--trainfile", 
                      dest="train_filename",
                      help="train FILE", 
                      default="./Databases/train1.txt",
                      metavar="FILE")
    
    parser.add_argument("--testfile", 
                      dest="test_filename",
                      help="test FILE", 
                      default="./Databases/test4.txt",
                      metavar="FILE")

    parser.add_argument("--nExamples", 
                      dest="nbExemples",
                      help="Number of exemples per Classe for the study",
                      type=int,  
                      default=10)

    parser.add_argument("--pTrain", 
                      dest="pourcentageTrain",
                      help="]0;1[, percent of training exemples",
                      type=float,  
                      default=0.6)

    parser.add_argument("--valid", 
                      dest="validation",
                      help="consideration of a validation set",
                      type=bool,  
                      default=False)

    parser.add_argument("--categorie", 
                      dest="categorie",
                      help="LFW or ORL", 
                      default="ORL")

    parser.add_argument("--stock", 
                      dest="stock",
                      help="1 si l'on veut stocker les données, 0 sinon", 
                      type=int,
                      default=0)

    parser.add_argument("--curv", 
                      dest="curv",
                      help="1 si l'on veut tracer les courbes, 0 sinon", 
                      type=int,
                      default=0)
    
    # sous parseur pour knn et nnet
    subparsers = parser.add_subparsers(title='Algorythms',
                                       description='Type of algorythm tou can use.',
                                       dest='algo_type')
    # KNN parser
    parser_knn = subparsers.add_parser('knn',
                                       help='use the k nearest neighbors algorythm',
                                       description='K Nearest Neighbors algorythm')
    parser_knn.add_argument("-k",
                            dest="k", 
                            type=int,
                            default=1,
                            help="number of neighbors")
    
    parser_knn.add_argument("-t", "--theta",
                            dest="theta",
                            type=float,
                            default=0.5,
                            help="gaussian kernel size")
    
    # NNET parser
    parser_nnet = subparsers.add_parser('nnet',
                                        help='use a neural network algorythm',
                                        description='Neural Network algorythm')
    parser_nnet.add_argument("--epoch",
                            dest="n_epoch", 
                            type=int,
                            default=100,
                            help="number of train epoch",
                            metavar="N")
    
    parser_nnet.add_argument("--hid",
                            dest="n_hidden", 
                            type=int,
                            default=10,
                            help="number of hidden neurons",
                            metavar="N")
    
    parser_nnet.add_argument("--batch",
                            dest="batch_size", 
                            type=int,
                            default=1,
                            help="size of the batch",
                            metavar="N")
    
    parser_nnet.add_argument("--lr",
                            dest="lr", 
                            type=float,
                            default=0.001,
                            help="learning rate",
                            metavar="NU")

    parser_nnet.add_argument("--wd", "--L2",
                            dest="wd", 
                            type=float,
                            default=0.0,
                            help="weight decay (L2 penality)",
                            metavar="ALPHA")

    # on parse la commande
    args = parser.parse_args()
    
    # On ne traite que les options connu (parsées dans opts)
    trainFile = args.train_filename
    testFile = args.test_filename
    debug_mode = args.verbose
    algo_type = args.algo_type.upper()
    categorie = args.categorie
    nbExemples = args.nbExemples
    stock = args.stock
    curv = args.curv
    pourcentageTrain = args.pourcentageTrain
    validation = bool(args.validation)


    #### Début du programme
    if algo_type == "KNN":
        K = args.k
        Theta = args.theta
        
        #### initialisation des abscisses et ordonnees #
        xVector = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        yVectorClassicTrain = []
        yVectorClassicValidation = []
        yVectorClassicTest = []
        yVectorKNNTrain = []
        yVectorKNNValidation = []
        yVectorKNNTest = []
        yVectorParzenTrain = []
        yVectorParzenValidation = []
        yVectorParzenTest = []

        #### construction main #
        faceReco = Main( K=K, Theta=Theta, trainFile=trainFile, testFile=testFile, validation=validation, categorie=categorie, stock=stock, curv=curv, pourcentageTrain=pourcentageTrain, nbExemples=nbExemples, debug_mode=debug_mode)
        if curv == 1 :
            indice = 0

            #### construction ordonnees et recuperation res
            for p in xVector:
                faceReco.pourcentageTrain = p
                listeRes = faceReco.main( algo=algo_type )
                yVectorClassicTrain.append( listeRes[0] )
                yVectorKNNTrain.append( listeRes[1] )
                yVectorParzenTrain.append( listeRes[2] )
                nbVectors = 6
                 ### Si validation
                if validation == 1 :
                    yVectorClassicValidation.append( listeRes[3] )
                    yVectorKNNValidation.append( listeRes[4] )
                    yVectorParzenValidation.append( listeRes[5] )
                    yVectorClassicTest.append( listeRes[6] )
                    yVectorKNNTest.append( listeRes[7] )
                    yVectorParzenTest.append( listeRes[8] )
                    nbVectors = 9
                else : 
                    yVectorClassicTest.append( listeRes[3] )
                    yVectorKNNTest.append( listeRes[4] )
                    yVectorParzenTest.append( listeRes[5] )
                xVector[indice] = np.max(( int(p * nbExemples), 1 ))
                indice += 1

            #### construction des conteneurs de nos 6 listes d'abscisses et ordonnees
            x=[]
            y=[]
            colorVect = ["g--", "b--", "r--", "g", "b", "r"] 
            legendVect = ["k=1 on train ", "k="+str(K)+" on train", "Parzen theta="+str(Theta)+" on train", "k=1 on test ", "k="+str(K)+" on test", "Parzen theta="+str(Theta)+" on test"]
            for i in range( nbVectors ):
                x.append(xVector)         
            y.append(yVectorClassicTrain)
            y.append(yVectorKNNTrain)
            y.append(yVectorParzenTrain)
            y.append(yVectorClassicTest)
            y.append(yVectorKNNTest)
            y.append(yVectorParzenTest)

            ### si validation
            if validation == 1:
                y.append(yVectorClassicTrain)
                y.append(yVectorKNNValidation)
                y.append(yVectorParzenValidation)

                colorVect.append("g-.")
                colorVect.append("b-.")
                colorVect.append("r-.")

                legendVect.append("k=1 on validation ")
                legendVect.append("k="+str(K)+" on validation")
                legendVect.append("Parzen theta="+str(Theta)+" on train")

            tools.drawCurves( x, y, colorVect, legendVect, title="Error Rate on Train/Test with "+categorie, xlabel="Examples p. class", ylabel="Error rate")

            #### construction fichier pour courbes ameliorees
            if stock == 1 :
                fichier = open("curvErrorKnn"+str(K)+categorie,"w")
                fichier.write("#xVector yVectorClassicTrain yVectorClassicTest yVectorKNNTrain yVectorKNNTest yVectorParzenTrain yVectorParzenTest\n")
                for i in range(len(xVector)) :
                    fichier.write(str(xVector[i])+" "+str(yVectorClassicTrain[i])+" "+str(yVectorClassicTest[i])+" "+str(yVectorKNNTrain[i])+" "+str(yVectorKNNTest[i])+" "+str(yVectorParzenTrain[i])+" "+str(yVectorParzenTest[i])+"\n")
                fichier.close()

        else : 
            listeRes = faceReco.main( algo=algo_type )

        
    
    elif algo_type == "NNET":
        n_epoch = args.n_epoch
        n_hidden = args.n_hidden
        batch = args.batch_size
        lr = args.lr
        wd = args.wd
        faceReco = Main( batch_size=batch, n_epoch=n_epoch, n_hidden=n_hidden, lr=lr, wd=wd, 
                         trainFile=trainFile, testFile=testFile, debug_mode=debug_mode, categorie=categorie, stock=stock, curv=curv, nbExemples=nbExemples)
        faceReco.main( algo=algo_type )

