from scipy.signal import find_peaks, savgol_filter
from scipy.optimize import curve_fit
from numpy.polynomial import Polynomial
import numpy as np
import sys

from os import path, makedirs


def gaussian(x, a, b, c, d):
    return a * np.exp(-((x - b) ** 2) / (2 * c**2)) + d


def calibrateData(calibrationSpectrum, referencePeaks):
    pixels = [int(pixel) for pixel in calibrationSpectrum[0]]
    axis = calibrationSpectrum[0]
    intensities = calibrationSpectrum[1]

    # Find peaks in calibration spectrum
    secondDerivation = savgol_filter(intensities, 11, 2, 2) * (-1)
    peaks, _ = find_peaks(secondDerivation)

    # Removing of non-relevant peaks and determining precise position of peaks
    newPeaks = []
    for peak in peaks:
        newPeak = []

        # Peak interval determination based on second derivation
        index = peak
        leftIndex = peak
        while index > max(peak - 10, 0) and secondDerivation[index] > 0:
            index -= 1
            leftIndex = index

        index = peak
        rightIndex = peak
        while (
            index < min(peak + 10, len(secondDerivation) - 1)
            and secondDerivation[index] > 0
        ):
            index += 1
            rightIndex = index

        # Discard peaks with insufficient interval
        if rightIndex - leftIndex + 1 < 6:
            # print(f"Skip interval\t[{peak},{intensities[peak]}]")
            continue

        # Control of peak intensity against backgroun noise
        noiseIntervalLeft = slice(max(leftIndex - 10, min(pixels)), leftIndex - 1)
        noiseIntervalRight = slice(rightIndex + 1, min(rightIndex + 10, max(pixels)))

        intervalSizeLeft = len(intensities[noiseIntervalLeft])
        if intervalSizeLeft > 5:
            averageLeft = np.average(intensities[noiseIntervalLeft])
            sigmaLeft = np.std(intensities[noiseIntervalLeft], ddof=1)

        intervalSizeRight = len(intensities[noiseIntervalRight])
        if intervalSizeRight > 5:
            averageRight = np.average(intensities[noiseIntervalRight])
            sigmaRight = np.std(intensities[noiseIntervalRight], ddof=1)

        if intervalSizeLeft <= 5:
            average = averageRight
            sigma = sigmaRight
        elif intervalSizeRight <= 5:
            average = averageLeft
            sigma = sigmaLeft
        elif averageLeft < averageRight:
            average = averageLeft
            sigma = sigmaLeft
        else:
            average = averageRight
            sigma = sigmaRight

        # Discard peaks with insufficient intensity
        if (intensities[peak] - average) / sigma < 5:
            # print(f"Skip intensity\t[{peak},{intensities[peak]}]")
            continue

        # Initial parameters for fit of peak
        backgroundInterval = slice(
            max(peak - 30, min(pixels)), min(peak + 30, max(pixels))
        )
        background = min(intensities[backgroundInterval])
        # print(f"Indexes\t\t[{rightIndex},{leftIndex}]")
        initialParameters = [
            intensities[peak] - background,  # intensity
            pixels[peak],  # position
            (pixels[rightIndex] - pixels[leftIndex]) / 3,  # width
            background,  # background
        ]

        # Fit of peak
        try:
            fitInterval = slice(leftIndex, rightIndex)
            fit, _ = curve_fit(
                gaussian,
                pixels[fitInterval],
                intensities[fitInterval],
                initialParameters,
            )
        except:
            # Discard the peak if fit fails
            # print(f"Skip fit fail\t[{peak},{intensities[peak]}]")
            continue

        # Discard the peak if its position falls out of the original interval
        if (fit[1] < pixels[leftIndex] or fit[1] > pixels[rightIndex]) or (
            fit[2] < 1 or fit[2] > 8
        ):
            # print(f"Skip pos out\t[{peak},{intensities[peak]}]")
            continue

        newPeak.append(fit[1])
        newPeak.append(fit[0] + fit[3] - background)
        newPeaks.append(newPeak)
    newPeaks = np.asarray(newPeaks)

    # Assigning of wavenumbers to peaks
    minShift = referencePeaks[0][0] - newPeaks[-1][0] - 100
    # print(f"{minShift=}\n")
    maxShift = referencePeaks[-1][0] - newPeaks[0][0] + 100
    # print(f"{maxShift=}\n")

    maxAgreement = -1
    agreementGraph = []
    for shift in np.arange(minShift, maxShift + 0.5, 0.5):
        progress = (shift - minShift) * 100 / (maxShift - minShift)
        sys.stdout.write("\r" + " " * 8)
        sys.stdout.write(f"\r{int(progress)}/100%")
        sys.stdout.flush()
        nearestPeaks = []
        agreement = 0
        lastWeight = 1
        for peak, _ in newPeaks:
            minDistance = -1  # ještě zkusit najít lepší způsob!!!
            for referencePeak, referenceWavelength in referencePeaks:
                distance = np.abs(peak + shift - referencePeak)
                if distance < minDistance or minDistance == -1:
                    minDistance = distance
                    nearestPeak = [peak, referenceWavelength, distance]
                else:
                    weight = 10 / (1 + nearestPeak[2] ** 2)
                    agreement += weight * lastWeight
                    lastWeight = weight
                    nearestPeaks.append(nearestPeak)
                    break
        agreementGraph.append([shift, agreement])

        if agreement > maxAgreement or maxAgreement == -1:
            maxAgreement = agreement
            bestShiftValues = {
                "shift": shift,
                "agreement": agreement,
                "assignedPeaks": nearestPeaks,
            }
    agreementGraph = np.asarray(agreementGraph)

    # Save log with agreement values (for CONTROL)
    # print(f"{agreementGraph=}")
    # if not path.exists("log"):
    #     makedirs("log")
    # with open(f"log/agreement.log", "w") as outputFile:
    #     for shift, agreement in agreementGraph:
    #         outputFile.write(f"{shift}")
    #         outputFile.write(f" {agreement}")
    #         outputFile.write(f"\n")

    # Duplicate wavenumber assignment check
    assignedPeaks = bestShiftValues["assignedPeaks"]
    i = 0
    while i < len(assignedPeaks) - 1:
        if assignedPeaks[i][2] > 20:
            del assignedPeaks[i]
            # print(f"Deleted dist {assignedPeaks[i]}")
        elif assignedPeaks[i][1] == assignedPeaks[i + 1][1]:
            if assignedPeaks[i][2] <= assignedPeaks[i + 1][2]:
                del assignedPeaks[i + 1]
                # print(f"Deleted dupe {assignedPeaks[i]}")
            else:
                del assignedPeaks[i]
                # print(f"Deleted dupe {assignedPeaks[i]}")
        else:
            i += 1
    if assignedPeaks[i][2] > 20:
        del assignedPeaks[i]
        # print(f"Deleted dist {assignedPeaks[i]}")
    pixelPeaks, assignedPeaks, _ = np.asarray(assignedPeaks).T

    # Save log with assigned peaks (for CONTROL)
    # with open(f"log/assignment.log", "w") as outputFile:
    #     for pixel, peak in zip(pixelPeaks, assignedPeaks):
    #         outputFile.write(f"{pixel}")
    #         outputFile.write(f" {peak}")
    #         outputFile.write(f"\n")

    # Fit of assigned wavenumbers by a polynomyial
    calibFunction, [residuals, _, _, _] = Polynomial.fit(
        pixelPeaks, assignedPeaks, 3, full=True
    )
    calibratedAxis = calibFunction(axis)

    # Goodness of fit
    totalSumSquares = ((assignedPeaks - np.mean(assignedPeaks)) ** 2).sum()
    rSquared = 1 - residuals / totalSumSquares
    # print(f"{calibFunction=}")

    # RETURN
    sys.stdout.write("\r" + " " * 8)
    return (calibratedAxis, bestShiftValues["shift"], rSquared)


def interpolateData(axis, spectra):
    newAxis = interpolateAxis(axis)
    newSpectra = []
    for spectrum in spectra:
        newSpectra.append(np.interp(newAxis, axis, spectrum))
    return [newAxis, newSpectra]


def interpolateAxis(axis):
    newAxisMin = np.ceil(axis[0])
    newAxisMax = np.floor(axis[-1])
    newAxis = np.arange(newAxisMin, newAxisMax + 1, 1)

    return newAxis


def getPeakInterval(peak, secondDerivation):
    index = peak
    leftIndex = peak
    while secondDerivation[index] > 0 and index > max(peak - 10, 0):
        index -= 1
        leftIndex = index

    index = peak
    rightIndex = peak
    while secondDerivation[index] > 0 and index < min(peak + 10, len(secondDerivation)):
        index += 1
        rightIndex = index

    return (leftIndex, rightIndex)
