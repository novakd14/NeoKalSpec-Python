import numpy as np
import os


def userInputLoadAllFiles():
    # Kalibrovat všechna spektra ve složce?
    while True:
        useAllFiles = input("Kalibrovat všechna spektra? Ano (y), Ne (n): (Y)").lower()
        if useAllFiles in ["y", "n", ""]:
            match useAllFiles:
                case "n":
                    useAllFiles = False
                    mess = "NE"
                case _:
                    useAllFiles = True
                    mess = "ANO"
            break

    print(f"Kalibrovat všechna spektra: {mess}")

    return useAllFiles


def userInputLoadOneFile():
    # Kalibrovat všechna spektra ve složce?
    fileName = input("Zadejte název souboru (bez přípony):")

    print(f"Nahrávám soubor se jménem: {fileName}")

    return fileName


def userInputCalibSpectrum():
    # Jedno kalibrační spektrum pro všechny spektra
    while True:
        oneCalibSpectrum = input(
            "Jedno kalibrační spektrum? Ano (y), Ne (n): (Y)"
        ).lower()
        if oneCalibSpectrum in ["y", "n", ""]:
            match oneCalibSpectrum:
                case "n":
                    oneCalibSpectrum = False
                    mess = "NE"
                case _:
                    oneCalibSpectrum = True
                    mess = "ANO"
            break

    print(f"Dodáno pouze jedno kalibrační spektrum: {mess}")

    return oneCalibSpectrum


def userInputGrid():
    # Jaká byla použita mřížka?
    while True:
        gridValue = input("Zvol použitou mřížku (1200 (1), 1800 (2)): (1)")
        if gridValue in ["1", "2", ""]:
            match gridValue:
                case "2":
                    grid = "g2 (1800)"
                case _:
                    grid = "g1 (1200)"
            break

    print(f"    Zvolena mřížka: {grid}")

    return grid


def userInputSaveSeparateFiles():
    while True:
        saveSeparateFiles = input(
            "Uložit každé spektrum do samostatného souboru? Ano (y), Ne (n): (Y)"
        ).lower()
        if saveSeparateFiles in ["y", "n", ""]:
            match saveSeparateFiles:
                case "n":
                    saveSeparateFiles = False
                    mess = "NE"
                case _:
                    saveSeparateFiles = True
                    mess = "ANO"
            break

    print(f"Uložit každé spektrum do samostatného souboru: {mess}")

    return saveSeparateFiles


def userInputRestartApp():
    while True:
        restartApp = input("Kalibrovat další spektra? Ano (y), Ne (n): (N)").lower()
        if restartApp in ["y", "n", ""]:
            match restartApp:
                case "y":
                    restartApp = True
                case _:
                    restartApp = False
            break

    return restartApp


def showFiles(path="."):
    return os.listdir(path)


def loadDataCSV(directory, file: str):
    file_path = f"{directory}/{file}"
    try:
        return np.loadtxt(file_path, usecols=(3, 4), delimiter=",")
    except Exception as error:
        pass
    try:
        return np.loadtxt(file_path, usecols=(0, 1), delimiter=",")
    except Exception as error:
        print("Špatný formát souboru.")


def loadDataSPE(directory, file: str):
    print("Ještě nefunguje!")
    return []


def splitData(data):
    split = []
    for i in range(0, len(data), 1340):
        split.append(data[i : i + 1340])
    return split


def averageData(data):
    pixels = data[0][0:1340]
    intensities = np.split(data[1], len(data[1]) / 1340)
    intensities = np.average(intensities, axis=0)
    return np.asarray([pixels, intensities])


def loadReferencePeaks(referencePath):
    return np.loadtxt(referencePath, usecols=(0, 1))
