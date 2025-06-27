# %% VERSION
# ALPHA: first testing version
#   DONE    Funguje pro mřížku 1200 (1), pro mřížku 1800 (2) chybí referenční pixelové hodnoty pásů.
#       Přidány a upraveny referenční hodnoty pro obě mřížky
#   PROBLEM Neprobíhají kontroly nahraných souborů!

# %% HEADER
print("!!! verze ALPHA: první testovací verze")
print('Kalibrace pro mřížky 1200 a 1800 vrypů/mm. Pro soubory CSV s oddělovačem ",".')
print("Výstup ve formátu TXT.")
print()
print("INSTRUKCE:")
print('Pro společné kalibrační spektrum pojmenovat kalibrační souboru "kalib.csv".')
print(
    'V případě specifických kalibračních spekter pro každé naměřené spektrum, přidat před jejich jméno "k" ("kjmeno.csv").'
)
print('Kalibrované spektra jsou uložené ve složce "CalibratedSpectra".')
print("-" * 60)

# %% IMPORT

# from components.output import outputSeparateFiles, outputOneFile
from numpy import asarray
import sys
import traceback
from os import path, makedirs

# %% INPUT
while True:
    try:
        from components.userInput import userInputLoadAllFiles

        calibrateAllFiles = userInputLoadAllFiles()
        print()

        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            dataDirectory = "."
            bundleDirectory = path.abspath(path.dirname(__file__))
        else:
            dataDirectory = "Data"
            bundleDirectory = "."

        from components.userInput import showFiles

        availableFiles = showFiles(dataDirectory)
        availableFiles = [file for file in availableFiles if file.endswith(".csv")]
        dataFiles, calibFiles = [], []

        if calibrateAllFiles:
            for file in availableFiles:
                if file.startswith("k_") or file.startswith("kalib"):
                    calibFiles.append(file)
                else:
                    dataFiles.append(file)
            from components.userInput import userInputCalibSpectrum

            oneCalibSpectrum = userInputCalibSpectrum()
            print()
        else:
            from components.userInput import userInputLoadOneFile

            fileName = userInputLoadOneFile()
            print()
            dataFiles = [
                dataFile
                for dataFile in availableFiles
                if dataFile.split(".")[0] == fileName
            ]
            calibFiles = [
                calibFile
                for calibFile in availableFiles
                if calibFile.split(".")[0] in ["kalib", f"k_{fileName}"]
            ]
            if len(calibFiles) != 0:
                calibFiles = [calibFiles[0]]
            oneCalibSpectrum = True
        from components.userInput import userInputGrid

        grid = userInputGrid()
        print()

        if calibrateAllFiles:
            from components.userInput import userInputSaveSeparateFiles

            saveSeparateFiles = userInputSaveSeparateFiles()
            print()
        else:
            saveSeparateFiles = True

        # %% DATA PREPARATION FOR CALIBRATION

        calibrationSpectra = []
        for calibFile in calibFiles:
            from components.userInput import loadDataCSV

            spectrum = loadDataCSV(dataDirectory, calibFile)
            calibrationSpectra.append([calibFile.split(".")[0], spectrum.T])

        dataSpectra = []
        for file in dataFiles:
            spectrum = loadDataCSV(dataDirectory, file)
            dataSpectra.append(spectrum.T[1])
        dataSpectra = asarray(dataSpectra)

        if grid == "g1 (1200)":
            referencePath = "referenceValues\\neonReference1200.csv"
        else:
            referencePath = "referenceValues\\neonReference1800.csv"
        referencePath = path.join(bundleDirectory, referencePath)

        from components.userInput import loadReferencePeaks

        referencePeaks = loadReferencePeaks(referencePath)

        # %% CALIBRATION

        calibratedAxes = []
        print(f"Spektrum\tPosun\tR^2")
        print("-" * 35)
        for calibFile, calibrationSpectrum in calibrationSpectra:
            from components.dataProcessing import calibrateData

            calibratedAxis, shift, residuals = calibrateData(
                calibrationSpectrum, referencePeaks
            )
            print(f"{calibFile}\t\t{shift:.2f}\t{residuals[0]:.4f}")
            calibratedAxes.append(calibratedAxis)
        calibratedAxes = asarray(calibratedAxes)
        print()

        # %% DATA PREPARATION FOR OUTPUT

        finalAxes, finalSpectra = [], []

        for axis, spectrum in zip(
            calibratedAxes
            if not oneCalibSpectrum
            else [calibratedAxes[0]] * len(dataSpectra),
            dataSpectra,
        ):
            from components.dataProcessing import interpolateData

            newAxis, newSpectrum = interpolateData(axis, spectrum)
            finalAxes.append(newAxis)
            finalSpectra.append(newSpectrum)

        if oneCalibSpectrum:
            from components.dataProcessing import interpolateAxis

            finalAxes = [interpolateAxis(calibratedAxes[0])]

        finalAxes = asarray(finalAxes)
        finalSpectra = asarray(finalSpectra)

        # %% OUTPUT

        folderName = "CalibratedSpectra"
        if not path.exists(folderName):
            makedirs(folderName)

        if saveSeparateFiles or not oneCalibSpectrum:
            from components.output import outputSeparateFiles

            outputSeparateFiles(
                finalAxes, finalSpectra, dataFiles, folderName, oneCalibSpectrum
            )
        else:
            from components.output import outputOneFile

            outputOneFile(finalAxes, finalSpectra, folderName)

        # END
        from components.userInput import userInputRestartApp

        restartApp = userInputRestartApp()
        if not restartApp:
            break
    except Exception as error:
        print("CHYBA: Ukončit aplikaci!")
        traceback.print_exc()
        print(error)
        print()
        input("Uknočit aplikaci.")
        break
