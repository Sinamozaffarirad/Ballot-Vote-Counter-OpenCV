# Paper Ballot Vote Counter (OpenCV)

My project for the Fundamentals of Computer Vision course at the University of Kashan.
Sina Mozaffari Rad, student ID 40021160214.

The program reads photos of filled paper ballots from a faculty council election (nine nominees and two
inspectors), finds which boxes are marked, checks each ballot against the election rules, catches the same
ballot photographed twice, and writes the final count to CSV files.

I used only classical image processing: thresholding, contours, Hough transforms and perceptual hashing. No
machine learning. Every decision can be traced back to a number (an area, a mean intensity, a line count), so
when a ballot is classified wrong it is easy to see why.

## How it works

<p align="center"><img src="docs/figures/pipeline.png" width="100%" alt="Processing pipeline"></p>

1. **Straighten the photo.** Ballots photographed by hand are often tilted. I detect edges with Canny, find
   line segments with the probabilistic Hough transform, take the median angle and rotate the image back. I pad
   the image before rotating, so the corners are not cut off.
2. **Pre-process.** Grayscale, a 5×5 Gaussian blur against paper texture, then an inverse binary threshold, so
   ink is white and paper is black.
3. **Find the checkboxes.** I keep only external contours with an area of 500–5000 px², an aspect ratio
   between 0.9 and 1.1, and exactly 4 corners after polygon approximation. This removes the text and the table
   lines and leaves only the boxes.
4. **Order the boxes** by (y, x), so each box belongs to one candidate.
5. **Decide if a box is marked.** People mark boxes in different ways, so I use two tests: the mean intensity
   inside the box (for filled boxes), or line segments found by Hough inside the box (for ✓ and ✗ marks).
   Either one is enough.
6. **Catch duplicates.** I compute a perceptual hash (pHash) of each image. Unlike a normal file hash, pHash
   still matches when the same photo is saved again or slightly changed.
7. **Check the rules.** A ballot is rejected if it is blank, if more than *N* nominees are marked, or if more
   than *n* inspectors are marked. *N* and *n* are asked when the program starts.
8. **Write the reports** with pandas, as UTF-8 CSV with BOM, so the Persian names open correctly in Excel.

## Results

<p align="center"><img src="docs/figures/results.png" width="90%" alt="Labeled ballots"></p>

Valid ballots get a number `#NNN`. Rejected ones get `RNNN` and the reason is written on the image. On the six
sample ballots:

| Output | Content |
|--------|---------|
| [`valid_votes.csv`](results/valid_votes.csv) | 3 valid ballots and the vote for each candidate |
| [`invalid_votes.csv`](results/invalid_votes.csv) | 3 rejected: one blank, one with too many inspectors, one duplicate photo |
| [`final_report.csv`](results/final_report.csv) | Number of valid ballots and total votes per candidate |

## Limitations

- The size and shape limits for the checkboxes are tuned to this ballot layout and these photo sizes. A
  different form or a photo from much further away would need new values.
- Boxes are matched to candidates by their order on the page. If one box is not detected, the following ones
  move to the wrong candidate. Matching each box to the name next to it would be more robust.
- Six ballots is a small test set. I did not measure accuracy on a larger set.

## Usage

```bash
pip install -r requirements.txt
python ballot_counter.py
```

1. Enter the maximum number of nominees (*N*, default 5) and inspectors (*n*, default 1) per ballot.
2. Select one or more ballot images. Samples are in `samples/`.
3. The program shows each processing step. The labelled images are saved next to the inputs as
   `*_labeled.jpg`, and the three CSV files are written to the current folder.

## Files

```
ballot_counter.py        The whole pipeline
samples/                 Ballot photos to try
results/                 Labelled outputs and CSV reports
docs/figures/            Images of each step
docs/make_figures.py     Builds the figures in this README
```
