import tkinter as tk
from tkinter import filedialog
import cv2
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from PIL import Image
import imagehash

# Check if a vote is a duplicate
def is_duplicate(vote, previous_votes):
    for prev_vote in previous_votes:
        if np.array_equal(vote, prev_vote):
            return True
    return False

# Check if the number of votes for nominees is valid
def is_valid_nominee_ballot(votes, max_nominees):
    nominee_votes = votes[:len(nominees)]
    return sum(nominee_votes) <= max_nominees

# Check if the number of votes for inspectors is valid
def is_valid_inspector_ballot(votes, max_inspectors):
    inspector_votes = votes[len(nominees):]
    return sum(inspector_votes) <= max_inspectors

# Check if the ballot is blank
def is_blank_ballot(votes):
    return sum(votes) == 0

# Calculate the perceptual hash of an image to detect duplicates
def calculate_phash(image_path):
    image = Image.open(image_path)
    hash_value = imagehash.phash(image)
    return hash_value

# Correct the rotation of the image if necessary
def correct_rotation(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=100, maxLineGap=10)
    if lines is not None:
        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
            angles.append(angle)
        median_angle = np.median(angles)
        if median_angle < -45:
            median_angle += 180
        elif median_angle > 45:
            median_angle -= 180

        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)

        # Increase the size of the image to avoid cropping
        diagonal = int(np.sqrt(w**2 + h**2))
        new_w, new_h = diagonal, diagonal
        padded_image = cv2.copyMakeBorder(image, (new_h - h) // 2, (new_h - h) // 2, (new_w - w) // 2, (new_w - w) // 2, cv2.BORDER_CONSTANT, value=(255, 255, 255))

        M = cv2.getRotationMatrix2D((new_w // 2, new_h // 2), median_angle, 1.0)
        rotated = cv2.warpAffine(padded_image, M, (new_w, new_h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))

        # Crop the image back to the original size
        start_x = (new_w - w) // 2
        start_y = (new_h - h) // 2
        cropped_rotated = rotated[start_y:start_y + h, start_x:start_x + w]
        return cropped_rotated

    return image

# Nominee and inspector names
nominees = [
    "عبدالحمید بامنیر",
    "حسین ابراهیم پور",
    "ابوالفضل حلوایی",
    "محسن بهپور",
    "بابک عالمی",
    "مهدی سبزواری",
    "روح الله نخعی",
    "علی عالی انوری",
    "رضا نوری"
]
inspectors = ["محمد ترکیها", "مهدی عباس محمدی"]

# Input maximum number of nominees and inspectors
max_nominees = int(input("Enter the maximum number of nominees to be selected (default is 5): ") or 5)
max_inspectors = int(input("Enter the maximum number of inspectors to be selected (default is 1): ") or 1)

# Ensure the total number of candidates is correct
total_candidates = len(nominees) + len(inspectors)

# Function to open a file dialog and select multiple image files
def select_files():
    root = tk.Tk()
    root.lift()  # Bring the window to the front
    root.attributes('-topmost', True)  # Ensure the window has focus
    root.withdraw()  # Hide the root window
    file_paths = filedialog.askopenfilenames(filetypes=[("Image files", "*.jpg;*.jpeg;*.png")])
    root.destroy()  # Properly close the Tkinter root window
    return file_paths

# Process each image to detect and validate votes
def process_image(image_path, vote_id, unique_hashes):
    image = cv2.imread(image_path)
    image = correct_rotation(image)
        
    plt.figure(figsize=(10, 10))
    plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    plt.title("Original Image")
    plt.show()

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    plt.figure(figsize=(10, 10))
    plt.imshow(gray, cmap='gray')
    plt.title("Gray Image")
    plt.show()

    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    plt.figure(figsize=(10, 10))
    plt.imshow(blurred, cmap='gray')
    plt.title("Blurred Image")
    plt.show()

    _, thresholded = cv2.threshold(blurred, 150, 255, cv2.THRESH_BINARY_INV)
    plt.figure(figsize=(10, 10))
    plt.imshow(thresholded, cmap='gray')
    plt.title("Thresholded Image")
    plt.show()

    # Find contours in the thresholded image
    contours, _ = cv2.findContours(thresholded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contour_image = image.copy()
    cv2.drawContours(contour_image, contours, -1, (0, 255, 0), 2)
    plt.figure(figsize=(10, 10))
    plt.imshow(cv2.cvtColor(contour_image, cv2.COLOR_BGR2RGB))
    plt.title("Contours Found")
    plt.show()

    # Filter and sort the contours to find the checkboxes
    squares = []
    for contour in contours:
        area = cv2.contourArea(contour)
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = w / float(h)

        if area > 500 and area < 5000 and 0.9 < aspect_ratio < 1.1:
            approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
            if len(approx) == 4:
                squares.append(approx)

    # Sort squares based on their position
    squares = sorted(squares, key=lambda x: (x[0][0][1], x[0][0][0]))

    # Check if squares are filled and label them
    votes = []
    square_image = image.copy()
    for i, square in enumerate(squares):
        mask = np.zeros_like(gray)
        cv2.drawContours(mask, [square], -1, 255, -1)
        mean_val = cv2.mean(gray, mask=mask)[0]

        # Apply additional check for tick marks
        tick_check = cv2.bitwise_and(thresholded, thresholded, mask=mask)
        lines = cv2.HoughLinesP(tick_check, 1, np.pi / 180, 50, minLineLength=10, maxLineGap=5)
        if mean_val < 180 or lines is not None:
            votes.append(1)
        else:
            votes.append(0)

        # Draw contours and votes on the original image
        color = (0, 255, 0) if mean_val < 180 or lines is not None else (255, 0, 0)
        cv2.drawContours(square_image, [square], -1, color, 2)
        label = "Voted" if mean_val < 180 or lines is not None else "Not Voted"
        label_color = (0, 255, 0) if mean_val < 180 or lines is not None else (255, 0, 0)
        x, y, w, h = cv2.boundingRect(square)
        cv2.putText(square_image, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, label_color, 2)

    plt.figure(figsize=(10, 10))
    plt.imshow(cv2.cvtColor(square_image, cv2.COLOR_BGR2RGB))
    plt.title("Squares and Votes Detected")
    plt.show()

    # Ensure the number of votes matches the number of nominees + inspectors
    if len(votes) > total_candidates:
        votes = votes[:total_candidates]
    elif len(votes) < total_candidates:
        votes += [0] * (total_candidates - len(votes))

    # Categorize votes
    valid_votes = []
    invalid_votes = []
    previous_votes = []

    # Calculate the hash of the current image
    current_hash = calculate_phash(image_path)

    # Check if the image is duplicate
    if current_hash in unique_hashes:
        invalid_votes.append((f"R{vote_id:03d}", "Duplicate Image", votes))
        cv2.putText(image, f"R{vote_id:03d} Duplicate Image", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)
    else:
        unique_hashes.add(current_hash)
        for i in range(0, len(votes), total_candidates):
            vote = votes[i:i+total_candidates]
            if i >= len(squares):
                break
            x, y, w, h = cv2.boundingRect(squares[i])  # Get bounding box for labeling
            if is_duplicate(vote, previous_votes):
                invalid_votes.append((f"R{vote_id:03d}", "Duplicate", vote))
                cv2.putText(image, f"R{vote_id:03d} Duplicate", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)
            elif is_blank_ballot(vote):
                invalid_votes.append((f"R{vote_id:03d}", "Blank Ballot", vote))
                cv2.putText(image, f"R{vote_id:03d} Blank Ballot", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)
            elif not (is_valid_nominee_ballot(vote, max_nominees)):
                invalid_votes.append((f"R{vote_id:03d}", f"Invalid count N>{max_nominees}", vote))
                cv2.putText(image, f"R{vote_id:03d} Invalid count N>{max_nominees}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)
            elif not (is_valid_inspector_ballot(vote, max_inspectors)):
                invalid_votes.append((f"R{vote_id:03d}", f"Invalid count n>{max_inspectors}", vote))
                cv2.putText(image, f"R{vote_id:03d} Invalid count n>{max_inspectors}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)
            else:
                valid_votes.append((f"#{vote_id:03d}", vote))
                previous_votes.append(vote)
                cv2.putText(image, f"#{vote_id:03d}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)

    # Display the labeled image
    plt.figure(figsize=(10, 10))
    plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    plt.title("Labeled Votes")
    plt.show()

    return valid_votes, invalid_votes, image


def generate_tables(valid_votes, invalid_votes):
    # Prepare data for the valid votes table
    valid_votes_data = []
    for vote_id, vote in valid_votes:
        row = [vote_id] + vote + [0] * (total_candidates - len(vote))  
        valid_votes_data.append(row)

    # Prepare data for the invalid votes table
    invalid_votes_data = []
    for vote_id, reason, vote in invalid_votes:
        row = [vote_id, reason] + vote + [0] * (total_candidates - len(vote))  
        invalid_votes_data.append(row)

    # Create DataFrame for valid votes
    df_valid_votes = pd.DataFrame(valid_votes_data, columns=['Vote ID'] + nominees + inspectors)

    # Create DataFrame for invalid votes
    df_invalid_votes = pd.DataFrame(invalid_votes_data, columns=['Vote ID', 'Reason'] + nominees + inspectors)

    return df_valid_votes, df_invalid_votes


def main():
    file_paths = select_files()
    all_valid_votes = []
    all_invalid_votes = []
    unique_hashes = set()
    vote_id = 1
    for file_path in file_paths:
        valid_votes, invalid_votes, labeled_image = process_image(file_path, vote_id, unique_hashes)
        all_valid_votes.extend(valid_votes)
        all_invalid_votes.extend(invalid_votes)
        vote_id += 1
        
        # Save the labeled image
        output_path = file_path.replace('.jpg', '_labeled.jpg').replace('.jpeg', '_labeled.jpeg').replace('.png', '_labeled.png')
        cv2.imwrite(output_path, labeled_image)

    # Generate the tables for valid and invalid votes
    df_valid_votes, df_invalid_votes = generate_tables(all_valid_votes, all_invalid_votes)

    # Calculate total votes for each nominee and inspector
    total_votes = df_valid_votes.drop(columns=['Vote ID']).sum(axis=0).to_frame().T
    total_votes.insert(0, 'Total', len(df_valid_votes))

    # Create the final report in the desired format
    final_report = total_votes.copy()
    final_report.columns = ['تعداد کل'] + nominees + inspectors

    # Save DataFrames to CSV
    df_valid_votes.to_csv('valid_votes.csv', index=False, encoding='utf-8-sig')
    df_invalid_votes.to_csv('invalid_votes.csv', index=False, encoding='utf-8-sig')
    final_report.to_csv('final_report.csv', index=False, header=True, encoding='utf-8-sig')

    print("Tables saved to CSV files: 'valid_votes.csv', 'invalid_votes.csv' and 'final_report.csv'")

if __name__ == "__main__":
    main()
