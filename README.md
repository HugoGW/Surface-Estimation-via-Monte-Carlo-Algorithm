# Surface-Estimation-via-Monte-Carlo-Algorithm

## Overview

This Python project is a **Pygame-based tool for interactively tracing shapes on a map** and estimating their real-world area using a **Monte Carlo sampling method**. It was originally created as a **demonstration tool to challenge flat-Earth proponents**, by allowing users to draw regions on a "flat Earth" map and compute their real surface area — revealing inconsistencies that arise from projecting a spherical Earth onto a 2D plane.

---

## Features

* Draw custom contours (polygons) with the mouse
* Set a real-world scale by clicking on a map's known distance (e.g., a scale bar)
* Estimate the enclosed area (in km²) using **Monte Carlo integration**
* Real-time updates during computation
* Handles open contours by automatically treating them as closed for the area calculation

---

## Requirements

* Python 3.x
* [Pygame](https://www.pygame.org/) (install via `pip install pygame`)

---

## Setup & Launch

1. Clone or download this repository.
2. Ensure you have Pygame installed:

   ```bash
   pip install pygame
   ```
3. Modify the image path in the code to point to your local map image file:

   ```python
   image_path = "/your/path/to/flat_earth.png"
   ```
4. Run the script:

   ```bash
   python your_script.py
   ```

---

## How to Use

### Step 1 — Drawing the Region

* Left-click and drag to draw a contour (polygon) on the map.
* The red line represents your current region.
* Release the mouse button to complete the trace.
* You can draw multiple traces if needed.

> **Note:** Even if your trace appears open, the Monte Carlo method treats the region as closed by logically connecting the first and last points.

---

### Step 2 — Setting the Scale

To convert from **pixels** to **kilometers**, you must define the scale:

1. Press `Enter` to enter **scale measurement mode**.
2. Left-click once at the **start of the scale bar** on the map.
3. Left-click again at the **end of the scale bar**.
4. A green line will appear, and you will be prompted to type the **real-world distance** in kilometers (e.g., `100`).
5. Press `Enter` again to validate.

This sets the pixel-to-kilometer ratio used for accurate area estimation.

---

### Step 3 — Estimating Area

* Once you've drawn your contour and set the scale, press `Enter` again to launch the Monte Carlo simulation.
* The tool randomly generates 100,000 sample points within the bounding box of your region and tests whether they lie inside the drawn shape.
* The estimated area in **km²** will be shown at the top-left of the screen and printed in the terminal.

---

## Behind the Scenes: How It Works

### Image and Display

* The tool loads a custom map image (`.png`) and uses its dimensions to size the Pygame window.
* Drawing is layered on top of the map surface.

### Drawing and Storing Contours

* Traces are recorded as lists of point tuples (x, y).
* All user-drawn traces are stored in the `traces` list.
* Each time the mouse is moved while pressed, new points are added to the current trace.

### Measuring Scale

* When measuring is enabled, two mouse clicks are interpreted as endpoints of a known-length segment.
* The pixel distance between these two points is computed and stored.
* The user is prompted to input the real distance in kilometers.
* A ratio (`scale_ratio`) is calculated in **km/pixel** and used for area conversion.

### Monte Carlo Estimation

* The bounding box of all points is computed.
* 100,000 random points (`num_samples = 100000`) are generated inside this bounding box.
* Each point is tested using the **ray casting algorithm** to determine if it lies inside the polygon.
* The ratio of points inside the region vs. total samples gives the approximate pixel area.
* This area is converted to **km²** using the square of the scale ratio.

### Automatic Contour Closure

* Even if the drawn contour is visually open, it is treated as **closed** by connecting the last point back to the first during inside/outside testing.
* This ensures the region is always interpreted as a proper polygon for area calculation.

---

## Controls Summary

| Key / Action      | Function                                                    |
| ----------------- | ----------------------------------------------------------- |
| Left Click & Drag | Draw a contour                                              |
| `Enter`           | Toggle between drawing, measuring, and launching estimation |
| `Delete`          | Remove last trace                                           |
| `Backspace`       | Edit typed scale value                                      |
| `Escape`          | Quit the program                                            |

---

## Example Use Case

Using a "flat Earth" map (azimuthal equidistant projection), you can:

* Trace the actual shape of a continent or region.
* Define a known scale from the map's scale bar.
* Compute the estimated area.
* Compare it to the real-world value to illustrate **distortion due to projection** — an inconsistency in the flat Earth model.

---

## Limitations

* The estimation is probabilistic and might vary slightly due to randomness.
* The accuracy depends on the number of samples (set to 100,000 by default).
* It currently supports only 2D polygon tracing; no elevation or 3D projection handling.

---

## Author & Purpose

This tool was developed to **visually and mathematically challenge the flat Earth model** by Hugo Alexandre (@Hugo_GW), demonstrating how projected maps distort real distances and areas. By using actual map scales and comparing computed areas, it serves as a simple but powerful educational and debunking tool.

---

## Illustrations
Here are some illustration to understand how the code works and the several steps to estimate surfaces and aeras
![image](https://github.com/user-attachments/assets/5872488c-2820-4867-a882-dc9ca520dd7c)
![image](https://github.com/user-attachments/assets/11777c17-f00f-42d5-a34c-3457f9467a80)
![image](https://github.com/user-attachments/assets/07f84f3e-c3bd-47ae-8e88-2ea62f6b535d)
![image](https://github.com/user-attachments/assets/c8df22d8-fa1d-4de0-a87a-f6c59f5cd43c)







