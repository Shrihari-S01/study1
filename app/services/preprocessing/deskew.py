from pathlib import Path
import cv2

class ImageCleaner:

    def clean(self, input_path: Path, output_path: Path) -> Path:

        image = cv2.imread(str(input_path))

        if image is None:
            raise ValueError(f"Could not read {input_path}")

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        gray = cv2.GaussianBlur(gray, (3,3), 0)

        gray = cv2.equalizeHist(gray)

        cv2.imwrite(str(output_path), gray)

        return output_path