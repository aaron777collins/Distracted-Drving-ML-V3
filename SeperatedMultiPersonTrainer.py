from cgi import test
from datetime import datetime as dt
import os.path as path
from typing import Tuple
import random

import numpy as np
import pandas as pd
from sklearn import metrics
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
from sklearn.gaussian_process import GaussianProcessClassifier
from sklearn.model_selection import cross_val_score
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.gaussian_process.kernels import RBF

from sklearn.metrics import accuracy_score
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
from sklearn.metrics import f1_score
from EasyMLLib.helper import Helper
from DataCleaner import DataCleaner
from sklearn.ensemble import AdaBoostClassifier, RandomForestClassifier, StackingClassifier
from matplotlib import pyplot as plt

from EasyMLLib.DataSplitter import DataSplitter
from EasyMLLib.logger import Logger
from EasyMLLib.ModelSaver import ModelSaver
from EasyMLLib.CSVWriter import CSVWriter

DIB_NAME = "DIB1"
DATASETS_PATH = path.join(DIB_NAME, 'dataRaw', 'ID')
SELECTED_DATA_SET_PATH = path.join("Single", "ET")
CONCAT_FILE_PATH = DIB_NAME
CONCAT_FILE_NAME = "concat-data"
CONCAT_FILE_EXT = ".csv"
CONCAT_FULLPATH_WITHOUT_EXT = path.join(CONCAT_FILE_PATH, CONCAT_FILE_NAME)

MODEL_FILE_NAME_BEGINNING = "model-"
MODEL_EXT = ".model"

# TESTS = ['accuracy', 'precision_micro', 'recall_micro', 'f1_micro', 'precision_macro', 'recall_macro', 'f1_macro']
TESTS = [accuracy_score, precision_score, recall_score, f1_score]
TESTS_WITH_SAMPLE_NAMES = []
for test in TESTS:
    TESTS_WITH_SAMPLE_NAMES.append(f"train-{test.__name__}")
    TESTS_WITH_SAMPLE_NAMES.append(f"val-{test.__name__}")
    TESTS_WITH_SAMPLE_NAMES.append(f"test-{test.__name__}")
#     TESTS_WITH_SAMPLE_NAMES.append(f"train-{test.__name__}-time")
#     TESTS_WITH_SAMPLE_NAMES.append(f"val-{test.__name__}-time")
#     TESTS_WITH_SAMPLE_NAMES.append(f"test-{test.__name__}-time")

# TESTS_WITH_SAMPLE_NAMES.append(f"train")
# TESTS_WITH_SAMPLE_NAMES.append(f"val")
# TESTS_WITH_SAMPLE_NAMES.append(f"test")
TESTS_WITH_SAMPLE_NAMES.append(f"train-time")
TESTS_WITH_SAMPLE_NAMES.append(f"val-time")
TESTS_WITH_SAMPLE_NAMES.append(f"test-time")

CSV_COLUMNS = ["Model", "Total Compile Time",
               "Total Sample Size", "Compile Time Per Sample"]
CSV_COLUMNS.extend(TESTS_WITH_SAMPLE_NAMES)

CSV_FORMAT = {CSV_COLUMNS[i]: i for i in range(len(CSV_COLUMNS))}


# PARAM
OVERWRITE_MODEL = True
MIN_ID = 1
MAX_ID = 28


class SeperatedMultiPersonTrainer:

    def getIdNumsArray(self) -> list:

      listOfIdNums = list(range(MIN_ID, MAX_ID +1))
      random.shuffle(listOfIdNums)
      return  listOfIdNums


    def main(self):

        # id = "concat"

        print(f"Creating Logger for model for all concatenated data")
        self.logger = Logger( f"Models-Scores-allModels-nobk-macro-concat-seperatedId.txt")
        self.csvWriter = CSVWriter(f"Models-Scores-allModels-nobk-macro-concat-seperatedId.csv", CSV_COLUMNS)

        self.logger.log("Getting clean data..")
        # data: pd.DataFrame = DataCleaner().getCleanData(id)

        listOfIdNums: list = self.getIdNumsArray()
        
        #Remember to change splices if MAX_ID changes
        train: pd.DataFrame = DataCleaner().getCleanDataFromSet(listOfIdNums[0:24]) #20 id's
        val: pd.DataFrame = DataCleaner().getCleanDataFromSet(listOfIdNums[24:26]) #4 id's
        test: pd.DataFrame =  DataCleaner().getCleanDataFromSet(listOfIdNums[26:28]) #4 id's

        self.logger.log( f"Train data is done with Id's {listOfIdNums[0:24]}")
        self.logger.log( f"Validation data is done with Id's {listOfIdNums[24:26]}")
        self.logger.log( f"Test data is done with Id's {listOfIdNums[26:28]}")

        allData: pd.DataFrame = DataCleaner().getCleanDataConcat()

        self.logger.log("Quick stats on clean data")
        Helper.quickDfStat(allData)

        self.logger.log("Getting Data Sets..")
        startTime = dt.now()

        #getting features and labels (aka answers)
        features, answers = DataSplitter().getAllFeaturesAndAnswers(allData)
        X_train, Y_train = DataSplitter().getAllFeaturesAndAnswers(train)
        X_val, Y_val = DataSplitter().getAllFeaturesAndAnswers(val)
        X_test, Y_test = DataSplitter().getAllFeaturesAndAnswers(test)

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
        ]

        classifiers = [
            DecisionTreeClassifier(),
            RandomForestClassifier(),
            MLPClassifier(),
        ]

        self.logger.log("Building many models from list the list of classifiers: ", classifierNames)

        for i, classifier in enumerate(classifiers):
            model_name = MODEL_FILE_NAME_BEGINNING + \
                f"{classifierNames[i]}-" + f"smp" + MODEL_EXT
            modelCompileTime = (dt.now()-dt.now())

            model = ModelSaver[StackingClassifier]().readModel(model_name)

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

            # self.logger.log("Testing model on val")
            # startTime = dt.now()
            # y_pred = model.predict(X_val)
            # timeElapsed = dt.now()-startTime
            # self.logger.log(f"Time elapsed: (hh:mm:ss:ms) {timeElapsed}")
            # row[CSV_FORMAT[f"val-time"]] = timeElapsed.total_seconds() / \
            #     len(X_val.index)
            # for test_type in TESTS:
            #     res = None
            #     if (test_type.__name__ == accuracy_score.__name__):
            #         res = test_type(Y_val, y_pred)
            #     else:
            #         res = test_type(Y_val, y_pred, average='macro')
            #     self.logger.log(f"val-{test_type.__name__}:", res)
            #     row[CSV_FORMAT[f"val-{test_type.__name__}"]] = res


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
    SeperatedMultiPersonTrainer().main()