from PIL import Image, ImageDraw, ImageFont
import os
from colorama import Fore, Style, init

init(autoreset = True)

OUTPUT_FOLDER_PNG = "OutputPNG"
OUTPUT_FOLDER_TXT = "OutputTXT"
INPUT_FOLDER = "Input"

# Sets import image to grayscale
def Grayify(image):
    return image.convert("L")

# Determines which character each pixel value should be set to
def PixelsToAscii(image, asciiChars, threshold):

    # Get image data and all of the ascii characters
    pixels = image.getdata()
    n = len(asciiChars)
    asciiStr = []

    # Loop through each pixel
    for pixel in pixels:

        # Check threshold (values below threshold will not get a char)
        if pixel < threshold:
            asciiStr.append(" ")

        # If above threshold convert that pixel value to a location in the ascii array
        # which best fits based on color value
        else:
            asciiIndex = int((pixel / 255) * (n - 1))
            asciiIndex = max((0, min(n - 1, asciiIndex)))
            asciiStr.append(asciiChars[asciiIndex])

    # Retruns a single string containing all chars
    return "".join(asciiStr)

# Calculates the number of rows and columns to preserve the original aspect ratio or pixel count
def CalculateAsciiGrid(origWidth, origHeight, font, scaleFactor):

    # Sets the target aspect ratio for image and allows for image scaling (1920x1080px -> 960x540px)
    targetWidth = int(origWidth * scaleFactor)
    targetHeight = int(origHeight * scaleFactor)

    # Gets width of the font
    bbox = font.getbbox("A")
    charWidth = abs(bbox[2] - bbox[0]) or 1
    charHeight = abs(bbox[3] - bbox[1]) or 1

    # Gets the approximate number of ascii chars per row and col
    rowsWidth = int(round(targetWidth / charWidth))
    colsHeight = int(round(targetHeight / charHeight))

    rowsWidth = max(1, rowsWidth)
    colsHeight = max(1, colsHeight)

    return rowsWidth, colsHeight, targetWidth, targetHeight

# Resizes import image to new dimensions
def resizeImage(image, newWidthChars, newHeightChars):
    return image.resize((newWidthChars, newHeightChars))

# Draws ascii string onto a png image with fractional spacing to avoid whitespace
def AsciiToImage(asciiStr, widthChars, targetWidth, targetHeight, font, bgColor, fontColor):

    lines = [asciiStr[i : i + widthChars] for i in range (0, len(asciiStr), widthChars)]
    heightChars = len(lines)

    # Draws ascii to export image
    image = Image.new("RGB", (targetWidth, targetHeight), color = bgColor)
    draw = ImageDraw.Draw(image)

    # Fractional spacing
    xStep = targetWidth / widthChars
    yStep = targetHeight / heightChars

    # Draw each line onto png
    for j, line in enumerate(lines):
        for i, c in enumerate(line):
            draw.text((i * xStep, j * yStep), c, fill = fontColor, font = font)

    return image

# Takes each import image(s), checks validity then calls all other functions
def ProcessImage(path, scaleFactor, fontSize, threshold, bgColor, fontColor, asciiChars):
    print(Fore.GREEN + f"\nProcessing: {path}")

    # Check for valid file input
    try:
        image = Image.open(path)
    except FileNotFoundError:
        print(path, "not found!")
        return
    except Exception as e:
        print(Fore.RED + "Error Opening Image:", e)
        return
    
    # Get image parameters
    origWidth, origHeight = image.size

    # Load font
    try:
        font = ImageFont.truetype("cour.ttf", fontSize)
    except:
        font = ImageFont.load_default()

    # Calculate ascii grid and image size
    WidthChars, heightChars, targetWidth, targetHeight = CalculateAsciiGrid(
        origWidth, origHeight, font, scaleFactor
    )

    # Resize image to new ascii grid size
    resizedImage = resizeImage(image, WidthChars, heightChars)

    # Convert to ascii
    asciiStr = PixelsToAscii(Grayify(resizedImage), asciiChars, threshold)

    # Save ascii text
    asciiText = "\n".join([asciiStr[i : i + WidthChars] for i in range (0, len(asciiStr), WidthChars)])

    # Output filenames
    baseName = os.path.splitext(os.path.basename(path))[0]
    outTxt = os.path.join(OUTPUT_FOLDER_TXT, f"{baseName}_ascii.txt")
    outPng = os.path.join(OUTPUT_FOLDER_PNG, f"{baseName}_ascii.png")

    # Save text file
    with open(outTxt, "w") as f:
        f.write(asciiText)

    # Save PNG
    asciiImage = AsciiToImage(asciiStr, WidthChars, targetWidth, targetHeight, font, bgColor, fontColor)
    asciiImage.save(outPng)

    print(Fore.GREEN + f"Saved TXT: {outTxt}")
    print(Fore.GREEN + f"Saved PNG: {outPng} ({asciiImage.size[0]}x{asciiImage.size[1]})")

def DrawMenuOption(menuLoc):
    if (menuLoc == 0):
        print("\nEnter the Scale Factor (e.g 1 for full-size, 0.5 for half-size, min 0.1)")
        print("Warning: you can upscale images, however expect longer process times and larger file sizes.")
    elif (menuLoc == 1):
        print("\nEnter Font Size (In Pixels)")
    elif (menuLoc == 2):    
        print("\nEnter the Background Color (rgb: e.g. 0 0 255 -> Blue).")
        print("You can also type \'bl\' for black, and \'wh\' for white.")
    elif (menuLoc == 3):
        print("\nEnter the Font Color (rgb: e.g. 0 0 255 -> Blue).")
        print("You can also type \'bl\' for black, and \'wh\' for white.")
    elif (menuLoc == 4):
        print("\nEnter the Threshold (Max: 255)")
        print("Lower values will result in images with a greater amount of ascii characters.")
        print("Recommended: 40-60 to preserve detail, while avoiding overcluttering.")
    else:
        print("\nEnter Ascii Type (1-4).")
        print("1) All Characters")
        print("2) Lines")
        print("3) Airthmetic Symbols")
        print("4) Numbers")

# Main function
def main():

    # Other var declaration
    count = 0
    uInput = None
    menuLoc = 0

    # Create folders if they dont already exist
    os.makedirs(INPUT_FOLDER, exist_ok = True)
    os.makedirs(OUTPUT_FOLDER_PNG, exist_ok = True)
    os.makedirs(OUTPUT_FOLDER_TXT, exist_ok = True)

    print(Fore.YELLOW + "\nAll images will be read from:", INPUT_FOLDER)
    print(Fore.MAGENTA + "All PNG exports will be saved to:", OUTPUT_FOLDER_PNG)
    print(Fore.MAGENTA + "All TXT exports will be saved to:", OUTPUT_FOLDER_TXT)
    print("=============================================\n")

    # Gather input files
    validExt = (".png", ".jpg", ".jpeg")
    files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith(validExt)]

    if not files:
        print(Fore.RED + "\nNo images were found in the input file.")
        print(Fore.RED + "Please check that the input files are in the right location and are of type (png, jpg, jpeg).\n")
        return
    
    print(Fore.CYAN + "Menu Navigation (e: exit, b: back)")

    while(True):

        if (menuLoc != 6):
            # Draw the selected menu option
            DrawMenuOption(menuLoc)

            # Other var input
            uInput = input()

            # Move back called
            if (uInput.lower() == 'b'):
                if (menuLoc > 0):
                    menuLoc -= 1
                else:
                    print(Fore.RED + "You cannot go back anymore.")
                continue

            # Exit called
            elif (uInput.lower() == 'e'):
                print(Fore.CYAN + "\nClosing Application, Thank You!\n")
                return 
            
            # Check for valid input (int)
            if (menuLoc != 2 and menuLoc != 3):
                if (menuLoc != 0):
                    try:
                        uInput = int(uInput)
                    except ValueError:
                        print(Fore.RED + f"\'{uInput}\'is not a valid input.")
                        continue

                # Check for valid input (float)
                else:
                    try:
                        uInput = float(uInput)
                    except ValueError:
                        print(Fore.RED + f"\'{uInput}\'is not a valid input.")
                        continue
            
            # Check for valid input (rgb)
            else:

                # First check for quick commands
                if (uInput.lower() == 'bl'):
                    rgb = (0, 0, 0)

                elif (uInput.lower() == 'wh'):
                    rgb = (255, 255, 255)

                else:
                    try:
                        # Create rgb value
                        rgb = tuple(map(int, uInput.split()))
                        
                        # Check for excactly three ints
                        if (len(rgb) != 3):
                            print(Fore.RED + f"You entered {len(rgb)} integers, when only 3 are expected.")
                            continue
                        
                        # Check that each value is within the bounds of rgb
                        if not all (0 <= x <= 255 for x in rgb):
                            raise ValueError(Fore.RED + "Values must be between 0 and 255.")

                    # Error for all other improper values
                    except ValueError as e:
                        print(Fore.RED + "You've entered an invalid response. Please try again.")
                        continue

        # Set scale
        if (menuLoc == 0):

            # Check that user doesn't enter a value too small
            if (uInput >= 0.1):
                scaleFactor = uInput
            else:
                print(Fore.RED + f"{uInput} is smaller than the allowed minimum.")
                continue

        # Set font size
        elif (menuLoc == 1):
            fontSize = uInput

        # Set bg color
        elif (menuLoc == 2):
            bgColor = rgb

        # Set font color
        elif (menuLoc == 3):
            fontColor = rgb

        # Set threshold
        elif (menuLoc == 4):
            threshold = uInput

        # Set ascii chars
        elif (menuLoc == 5):
            if (uInput == 1):
                asciiChars = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/|()1{}[]?-_+~<>i!lI;:,\"^`'. "
            elif (uInput == 2):
                asciiChars = "+-|/\\_="
            elif (uInput == 3):
                 asciiChars = ".:-=+*#%@"
            elif (uInput == 4):
                asciiChars = "0123456789"
            else:
                print(f"\n\'{uInput}\'is not a valid option.")
                continue

        # Process files
        else:

            # Process each file in folder
            for f in files:
                ProcessImage(os.path.join(INPUT_FOLDER, f), scaleFactor, fontSize, threshold, bgColor, fontColor, asciiChars)
                count += 1
                print(Fore.GREEN + f"{count} of {len(files)} completed.")

            # Process compelete
            print(Fore.GREEN + "\nProcess Has Completed.")

            # Prompt user
            print(Fore.CYAN + "Would you like to re-process the images?(y/n)")

            # Check for valid response
            while (True):
                
                # Check for digits
                uInput = input()
                if (uInput.isdigit()):
                    print(Fore.RED + f"\'{uInput}\'is not a valid input.")

                # Close application
                elif (uInput.lower() == 'n'):
                    print(Fore.CYAN + "\nClosing Application, Thank You!")
                    return 
                
                # Re-process images
                elif (uInput.lower() == 'y'):
                    menuLoc = 0
                    count = 0
                    break
                
                # Invalid input (non digit)
                else:
                    print(Fore.RED + f"\n\'{uInput}\'is not a valid input.")
            continue

        # Increment menu location
        menuLoc += 1

# Call main
if __name__ == "__main__":
    main()