import os
from numpy import asarray


def outputSeparateFiles(axes, allSpectra, files, folderName, oneCalibSpectrum):
    for file, axis, spectra in zip(
        files,
        axes if not oneCalibSpectrum else [axes[0]] * len(files),
        allSpectra,
    ):
        fileName, _ = os.path.splitext(file)
        newFile = f"{folderName}/{fileName}.txt"

        with open(newFile, "w") as outputFile:
            for point, row in zip(axis, asarray(spectra).T):
                outputFile.write(f"{point}")
                for cell in row:
                    outputFile.write(f" {cell}")
                outputFile.write("\n")
        print(f"Data has been written to {newFile}.")


def outputOneFile(axes, allSpectra, folderName):
    spectra = []
    for oneFile in allSpectra:
        for spectrum in oneFile:
            spectra.append(spectrum)
    newFile = f"{folderName}/calibratedSpectra.txt"
    with open(newFile, "w") as outputFile:
        for point, row in zip(axes[0], asarray(spectra).T):
            outputFile.write(f"{point}")
            for cell in row:
                outputFile.write(f" {cell}")
            outputFile.write("\n")

    print(f"Data has been written to {newFile}.")
