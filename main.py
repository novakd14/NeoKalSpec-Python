# %% VERSION
# ALPHA: first testing version
#   DONE    Funguje pro mřížku 1200 (1), pro mřížku 1800 (2) chybí referenční pixelové hodnoty pásů.
#       Přidány a upraveny referenční hodnoty pro obě mřížky
#   PROBLEM Neprobíhají kontroly nahraných souborů!

# %% HEADER
print("!!! verze ALPHA: první testovací verze")
print(
    'Kalibrace pro mřížky 1200 a 1800 vrypů/mm. Pro soubory CSV s oddělovačem "," a dvěmi, nebo pěti sloupci.'
)
print("Výstup ve formátu TXT.")
print()
print("INSTRUKCE:")
print('Pro společné kalibrační spektrum pojmenovat kalibrační souboru "kalib.csv".')
print(
    'V případě specifických kalibračních spekter pro každé naměřené spektrum, přidat před jejich jméno "k_" ("k_jmeno.csv").'
)
print('Kalibrované spektra jsou uložené ve složce "CalibratedSpectra".')
print("-" * 60)

# %% IMPORT

from components.userInput import (
    loadDataCSV,
    splitData,
    averageData,
    loadReferencePeaks,
    showFiles,
    userInputLoadAllFiles,
    userInputLoadOneFile,
    userInputCalibSpectrum,
    userInputGrid,
    userInputSaveSeparateFiles,
    userInputRestartApp,
)
from components.dataProcessing import (
    calibrateData,
    interpolateData,
    interpolateAxis,
)
from components.output import outputSeparateFiles, outputOneFile
from numpy import asarray
import sys
import traceback
from os import path, makedirs

# %% INPUT
while True:
    try:
        calibrateAllFiles = userInputLoadAllFiles()
        print()

        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            dataDirectory = "."
            bundleDirectory = path.abspath(path.dirname(__file__))
        else:
            dataDirectory = "Data"
            bundleDirectory = "."

        availableFiles = showFiles(dataDirectory)
        availableFiles = [file for file in availableFiles if file.endswith(".csv")]
        dataFiles, calibFiles = [], []

        if calibrateAllFiles:
            for file in availableFiles:
                if file.startswith("k_") or file.startswith("kalib"):
                    calibFiles.append(file)
                else:
                    dataFiles.append(file)
            oneCalibSpectrum = userInputCalibSpectrum()
            print()
        else:
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

        grid = userInputGrid()
        print()

        if calibrateAllFiles:
            saveSeparateFiles = userInputSaveSeparateFiles()
            print()
        else:
            saveSeparateFiles = True

        # %% DATA PREPARATION FOR CALIBRATION

        maxLen = 0
        calibrationSpectra = []
        for calibFile in calibFiles:
            if len(calibFile.split(".")[0]) > maxLen:
                maxLen = len(calibFile.split(".")[0])
            spectrum = loadDataCSV(dataDirectory, calibFile).T
            if len(spectrum[0]) > 1340:
                spectrum = averageData(spectrum)
            calibrationSpectra.append([calibFile.split(".")[0], spectrum])

        dataSpectra = []
        for file in dataFiles:
            spectrum = loadDataCSV(dataDirectory, file).T
            dataSpectra.append(splitData(spectrum[1]))

        if grid == "g1 (1200)":
            referencePath = "referenceValues/neonReference1200.csv"
        else:
            referencePath = "referenceValues/neonReference1800.csv"
        referencePath = path.join(bundleDirectory, referencePath)
        referencePeaks = loadReferencePeaks(referencePath)

        # %% CALIBRATION
        calibratedAxes = []
        print("Spektrum\t".expandtabs(8), end="")
        print("\t".expandtabs(8) * (max(0, maxLen // 8 - 1)), end="")
        print("Posun\tR^2".expandtabs(8))
        print("-" * (max(2, maxLen // 8 + 1) * 8 + 16))
        for calibFile, calibrationSpectrum in calibrationSpectra:
            calibratedAxis, shift, residuals = calibrateData(
                calibrationSpectrum, referencePeaks
            )
            print(f"\r{calibFile}\t".expandtabs(8), end="")
            if maxLen // 8 == 0:
                print("\t".expandtabs(8), end="")
            try:
                print(f"{shift:.2f}\t{residuals[0]:.4f}".expandtabs(8), end="")
            except:
                print(f"{shift:.2f}\t1".expandtabs(8), end="")
            calibratedAxes.append(calibratedAxis)
            print()
        calibratedAxes = asarray(calibratedAxes)

        # %% DATA PREPARATION FOR OUTPUT

        finalAxes, finalSpectra = [], []

        for axis, spectra in zip(
            (
                calibratedAxes
                if not oneCalibSpectrum
                else [calibratedAxes[0]] * len(dataSpectra)
            ),
            dataSpectra,
        ):
            newAxis, newSpectra = interpolateData(axis, spectra)
            finalAxes.append(asarray(newAxis))
            finalSpectra.append(asarray(newSpectra))

        if oneCalibSpectrum:
            finalAxes = [interpolateAxis(calibratedAxes[0])]

        # finalAxes = asarray(finalAxes)
        # finalSpectra = asarray(finalSpectra)

        # %% OUTPUT

        folderName = "CalibratedSpectra"
        if not path.exists(folderName):
            makedirs(folderName)

        if saveSeparateFiles or not oneCalibSpectrum:
            outputSeparateFiles(
                finalAxes,
                finalSpectra,
                dataFiles,
                folderName,
                oneCalibSpectrum,
            )
        else:
            outputOneFile(finalAxes, finalSpectra, folderName)

        # END
        restartApp = userInputRestartApp()
        if not restartApp:
            break
    except Exception as error:
        print("CHYBA: Ukončit aplikaci!")
        traceback.print_exc()
        print(error)
        print()
        input("Ukončit aplikaci.")
        break
