import cv2
import numpy as np

class FieldAnalyst:
    def __init__(self, pitch_length, pitch_width):
        self.pitch_length = pitch_length
        self.pitch_width = pitch_width
        self.homography_matrix = None

    def calibrate(self, src_points):
        """
        src_points: 4 pontos detetados na imagem (cantos do campo)
        """
        # Coordenadas reais do campo em metros (0,0 é o topo esquerdo)
        dst_points = np.array([
            [0, 0],
            [self.pitch_length, 0],
            [self.pitch_length, self.pitch_width],
            [0, self.pitch_width]
        ], dtype=np.float32)

        self.homography_matrix, _ = cv2.findHomography(np.array(src_points), dst_points)

    def pixel_to_meters(self, x, y):
        if self.homography_matrix is None:
            return x, y

        point = np.array([[[x, y]]], dtype=np.float32)
        transformed = cv2.perspectiveTransform(point, self.homography_matrix)
        return transformed[0][0][0], transformed[0][0][1]
