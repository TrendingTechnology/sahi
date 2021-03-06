import copy

import numpy as np

from sahi.annotation import ObjectAnnotation
from sahi.utils.torch import to_float_tensor, torch_stack


class PredictionScore:
    def __init__(self, score: float):
        """
        Arguments:
            score: prediction score between 0 and 1
        """
        # if score is a numpy object, convert it to python variable
        if type(score).__module__ == "numpy":
            score = copy.deepcopy(score).tolist()
        # set score
        self.score = score

    def is_greater_than_threshold(self, threshold):
        """
        Check if score is greater than threshold
        """
        return self.score > threshold

    def __repr__(self):
        return f"PredictionScore: <score: {self.score}>"


class ObjectPrediction(ObjectAnnotation):
    """
    Class for handling detection model predictions.
    """

    def __init__(
        self,
        bbox: list,
        score: float,
        category_id: int,
        category_name=None,
        bool_mask=None,
        shift_amount: list = [0, 0],
        full_image_size: list = [1024, 1024],
    ):
        """
        Creates ObjectPrediction from bbox, score, category_id, category_name, bool_mask.

        Arguments:
            bbox: list
                [minx, miny, maxx, maxy]
            score: float
                Prediction score between 0 and 1
            category_id: int
                ID of the object category
            category_name: str
                Name of the object category
            bool_mask: np.ndarray
                2D boolean mask array. Should be None if model doesn't output segmentation mask.
            shift_amount: list
                To shift the box and mask predictions from sliced image
                to full sized image, should be in the form of [shift_x, shift_y]
            full_image_size: list
                Size of the full image after shifting, should be in
                the form of [height, width]
        """
        self.score = PredictionScore(score)
        super().__init__(
            bbox=bbox,
            category_id=category_id,
            bool_mask=bool_mask,
            category_name=category_name,
            shift_amount=shift_amount,
            full_image_size=full_image_size,
        )

    def get_shifted_object_prediction(self):
        """
        Returns shifted version ObjectPrediction.
        Shifts bbox and mask coords.
        Used for mapping sliced predictions over full image.
        """
        if self.mask:
            return ObjectPrediction(
                bbox=self.bbox.get_shifted_box().to_voc_bbox(),
                category_id=self.category.id,
                score=self.score.score,
                bool_mask=self.mask.get_shifted_mask().bool_mask,
                category_name=self.category.name,
                shift_amount=[0, 0],
                full_image_size=self.mask.get_shifted_mask().get_full_image_size(),
            )
        else:
            return ObjectPrediction(
                bbox=self.bbox.get_shifted_box().to_voc_bbox(),
                category_id=self.category.id,
                score=self.score.score,
                bool_mask=None,
                category_name=self.category.name,
                shift_amount=[0, 0],
                full_image_size=None,
            )

    def __repr__(self):
        return f"""ObjectPrediction<
    bbox: {self.bbox},
    mask: {self.mask},
    score: {self.score},
    category: {self.category}>"""


class PredictionInput:
    def __init__(
        self,
        image_list,
        shift_amount_list=None,
        full_image_size=None,
    ):
        """
        Arguments:
            image_list: list of images to be predicted
            shift_amount_list: To shift the box and mask predictions from sliced image to full sized image, should be in the form of [shift_x, shift_y]
            full_image_size: Size of the full image after shifting, should be in the form of [height, width]

        image_list and shift_amount_list should have same length
        """
        self.image_list = image_list
        image_tensor_list = []
        for image in image_list:
            # normalize image
            image = image / np.max(image)
            # convert numpy image to tensor
            image_tensor_list.append(to_float_tensor(image))
        # create batch tensor
        batch_image_tensor = torch_stack(tuple(image_tensor_list), dim=0)
        self.batch_image_tensor = batch_image_tensor
        # set other properties
        if shift_amount_list:
            self.shift_amount_list = shift_amount_list
        else:
            self.shift_amount_list = [[0, 0] for ind in range(len(image_list))]
        self.full_image_size = full_image_size
