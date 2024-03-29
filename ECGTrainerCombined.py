from cgi import test
from datetime import datetime as dt
import os.path as path
from typing import Tuple

import numpy as np
import pandas as pd
from sklearn import metrics
from sklearn.calibration import CalibratedClassifierCV, LinearSVC
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis, QuadraticDiscriminantAnalysis
from sklearn.gaussian_process import GaussianProcessClassifier
from sklearn.linear_model import LogisticRegression, PassiveAggressiveClassifier, Perceptron, RidgeClassifier, SGDClassifier
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.multiclass import OneVsOneClassifier, OneVsRestClassifier
from sklearn.naive_bayes import BernoulliNB, ComplementNB, GaussianNB, MultinomialNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC, NuSVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.gaussian_process.kernels import RBF

from sklearn.metrics import accuracy_score
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
from sklearn.metrics import f1_score
from EasyMLLib.helper import Helper
from ECGDataCleaner import ECGDataCleaner
from sklearn.ensemble import AdaBoostClassifier, BaggingClassifier, ExtraTreesClassifier, GradientBoostingClassifier, HistGradientBoostingClassifier, RandomForestClassifier, StackingClassifier, VotingClassifier
from matplotlib import pyplot as plt

from EasyMLLib.DataSplitter import DataSplitter
from EasyMLLib.logger import Logger
from EasyMLLib.ModelSaver import ModelSaver
from EasyMLLib.CSVWriter import CSVWriter

DIB_NAME = "DIB2"
DATASETS_PATH = path.join("data", DIB_NAME, 'dataRaw') #good
SELECTED_DATA_SET_PATH = path.join("Single", "ET")
CONCAT_FILE_PATH = path.join("data", DIB_NAME)
CONCAT_FILE_NAME = "concat-data"
CONCAT_FILE_EXT = ".csv"
CONCAT_FULLPATH_WITHOUT_EXT = path.join(CONCAT_FILE_PATH, CONCAT_FILE_NAME) #data data/DIB2/concat-data

MODEL_FILE_NAME_BEGINNING = "model-"
MODEL_EXT = ".model"

TESTS = [accuracy_score, precision_score, recall_score, f1_score]
TESTS_WITH_SAMPLE_NAMES = []
for test in TESTS:
    TESTS_WITH_SAMPLE_NAMES.append(f"train-{test.__name__}")
    TESTS_WITH_SAMPLE_NAMES.append(f"val-{test.__name__}")
    TESTS_WITH_SAMPLE_NAMES.append(f"test-{test.__name__}")

TESTS_WITH_SAMPLE_NAMES.append(f"train-time")
TESTS_WITH_SAMPLE_NAMES.append(f"val-time")
TESTS_WITH_SAMPLE_NAMES.append(f"test-time")

CSV_COLUMNS = ["Model", "Total Compile Time",
               "Total Sample Size", "Compile Time Per Sample"]
CSV_COLUMNS.extend(TESTS_WITH_SAMPLE_NAMES)

CSV_FORMAT = {CSV_COLUMNS[i]: i for i in range(len(CSV_COLUMNS))}


# PARAM
OVERWRITE_MODEL = True

CLASSIFIER_NAME = "classifier"


class ECGTrainerCombined:
    def getFeaturesAndAnswers(self, data:pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        return (data.drop([CLASSIFIER_NAME], axis=1), data[CLASSIFIER_NAME])

    def main(self):

        # id = "concat"

        print(f"Creating Logger for model for all concatenated ecg data")
        self.logger = Logger( f"Models-Scores-allModels-nobk-macro-concat-ECG.txt")
        self.csvWriter = CSVWriter(f"Singular6-Models-Scores-allModels-nobk-macro-ECG.csv", CSV_COLUMNS)

        self.logger.log("Getting clean data..")
        data: pd.DataFrame = ECGDataCleaner().gatherECGDataSingular(6)
        data.drop(['Time'], axis=1, inplace=True)
        
        self.logger.log("Quick stats on clean data")
        Helper.quickDfStat(data)

        self.logger.log("Getting Data Sets..")
        startTime = dt.now()

        features, answers = self.getFeaturesAndAnswers(data)
        
        X_train, X_test, Y_train, Y_test = train_test_split(features, answers, test_size=0.4, random_state=42)
        X_val, X_test, Y_val, Y_test = train_test_split(X_test, Y_test, test_size=0.5, random_state=42)

        # Aarons code suscks so commenting it out
        # X_train, Y_train, X_val, Y_val, X_test, Y_test = DataSplitter().getTrainValTestSplit(data)


        self.logger.log( f"Time elapsed: (hh:mm:ss:ms) {dt.now()-startTime}")

        self.logger.log( "Quick stats on features and answers for the train-val-test split")
        Helper.quickDfArrStat([X_train, Y_train])
        Helper.quickDfArrStat([X_val, Y_val])
        Helper.quickDfArrStat([X_test, Y_test])

        self.logger.log( "Verifying the features and answers for the sets add up")
        
        # self.logger.log("Verifying X..")
        featureArr = []
        for df in [X_train, X_val, X_test]:
            val = round(len(df.index)/len(features.index), 3)
            featureArr.append(val)
            # self.logger.log(f"{val}")

        # self.logger.log("Verifying Y..")
        answerArr = []
        for df in [Y_train, Y_val, Y_test]:
            val = round(len(df.index)/len(answers.index), 3)
            answerArr.append(val)
            # self.logger.log(f"{val}")

        self.logger.log("Adding up X")
        sum = 0
        for x in featureArr:
            sum += x
        self.logger.log(f"Sum: {sum}")
        self.logger.log("Adding up Y")
        sum = 0
        for y in answerArr:
            sum += y
        self.logger.log(f"Sum: {sum}")

        classifierNames = [
            "Decision Tree",
            "Random Forest",
            "Neural Net",
            "LogisticRegression",
            "GaussianNB",
            "SVC",
            "KNeighborsClassifier",
            "GradientBoostingClassifier",
            "AdaBoostClassifier",
            "BaggingClassifier",
            "LinearDiscriminantAnalysis",
            "QuadraticDiscriminantAnalysis",
            "RidgeClassifier",
            "SGDClassifier",
            "PassiveAggressiveClassifier",
            "Perceptron",
            "BernoulliNB",
            "ComplementNB",
            "MultinomialNB",
            "CalibratedClassifierCV",
            "HistGradientBoostingClassifier",
            "NuSVC",
            "LinearSVC",
            "ExtraTreesClassifier"
        ]

        classifiers = [
            DecisionTreeClassifier(),
            RandomForestClassifier(),
            MLPClassifier(),
            LogisticRegression(),
            GaussianNB(),
            SVC(),
            KNeighborsClassifier(),
            GradientBoostingClassifier(),
            AdaBoostClassifier(),
            BaggingClassifier(),
            LinearDiscriminantAnalysis(),
            QuadraticDiscriminantAnalysis(),
            RidgeClassifier(),
            SGDClassifier(),
            PassiveAggressiveClassifier(),
            Perceptron(),
            BernoulliNB(),
            ComplementNB(),
            MultinomialNB(),
            CalibratedClassifierCV(),
            HistGradientBoostingClassifier(),
            NuSVC(),
            LinearSVC(),
            ExtraTreesClassifier(),
        ]

        self.logger.log("Building many models from list the list of classifiers: ", classifierNames)

        for i, classifier in enumerate(classifiers):
            model_name = MODEL_FILE_NAME_BEGINNING + \
                f"{classifierNames[i]}-" + f"" + MODEL_EXT
            modelCompileTime = (dt.now()-dt.now())

            # model = ModelSaver[StackingClassifier]().readModel(model_name)
            model = None 

            if(not model or OVERWRITE_MODEL):
                self.logger.log(f"Building Model on: {classifierNames[i]}")

                startTime = dt.now()
                model = self.buildModel(X_train, Y_train, classifier)
                modelCompileTime = (dt.now()-startTime)
                self.logger.log(
                    f"Time elapsed: (hh:mm:ss:ms) {modelCompileTime}")

                self.logger.log(f"Saving Model as: {model_name}")
                startTime = dt.now()
                ModelSaver().saveModel(model, model_name)
                self.logger.log(
                    f"Time elapsed: (hh:mm:ss:ms) {dt.now()-startTime}")

            row = [" "] * len(CSV_COLUMNS)
            row[CSV_FORMAT["Model"]] = classifierNames[i]
            row[CSV_FORMAT["Total Compile Time"]] = modelCompileTime
            row[CSV_FORMAT["Total Sample Size"]] = len(X_train.index)
            row[CSV_FORMAT["Compile Time Per Sample"]
                ] = modelCompileTime.total_seconds() / len(X_train.index)

            self.logger.log(f"Possible tests:", metrics.SCORERS.keys())

            self.logger.log("Testing model on Train")
            startTime = dt.now()
            y_pred = model.predict(X_train)
            timeElapsed = dt.now()-startTime
            self.logger.log(f"Time elapsed: (hh:mm:ss:ms) {timeElapsed}")
            row[CSV_FORMAT[f"train-time"]] = timeElapsed.total_seconds() / \
                len(X_train.index)
                
            for test_type in TESTS:
                res = None
                if (test_type.__name__ == accuracy_score.__name__):
                    res = test_type(Y_train, y_pred)
                else:
                    res = test_type(Y_train, y_pred, average='macro')
                self.logger.log(f"train-{test_type.__name__}:", res)
                row[CSV_FORMAT[f"train-{test_type.__name__}"]] = res

            self.logger.log("Testing model on val")
            startTime = dt.now()
            y_pred = model.predict(X_val)
            timeElapsed = dt.now()-startTime
            self.logger.log(f"Time elapsed: (hh:mm:ss:ms) {timeElapsed}")
            row[CSV_FORMAT[f"val-time"]] = timeElapsed.total_seconds() / \
                len(X_val.index)
            for test_type in TESTS:
                res = None
                if (test_type.__name__ == accuracy_score.__name__):
                    res = test_type(Y_val, y_pred)
                else:
                    res = test_type(Y_val, y_pred, average='macro')
                self.logger.log(f"val-{test_type.__name__}:", res)
                row[CSV_FORMAT[f"val-{test_type.__name__}"]] = res


            self.logger.log("Testing model on test")
            startTime = dt.now()
            y_pred = model.predict(X_test)
            timeElapsed = dt.now()-startTime
            self.logger.log(f"Time elapsed: (hh:mm:ss:ms) {timeElapsed}")
            row[CSV_FORMAT[f"test-time"]] = timeElapsed.total_seconds() / \
                len(X_test.index)
            for test_type in TESTS:
                res = None
                if (test_type.__name__ == accuracy_score.__name__):
                    res = test_type(Y_test, y_pred)
                else:
                    res = test_type(Y_test, y_pred, average='macro')
                self.logger.log(f"test-{test_type.__name__}:", res)
                row[CSV_FORMAT[f"test-{test_type.__name__}"]] = res

            self.csvWriter.addRow(row)


    def buildModel(self, features: pd.DataFrame, answers: pd.DataFrame, model):
        # from tutorial: https://machinelearningmastery.com/calculate-feature-importance-with-python/

        # fit the model
        model.fit(features, answers)

        return model


if __name__ == "__main__":
    ECGTrainerCombined().main()