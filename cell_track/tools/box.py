def extract_xyrange(box):
    """
    Gets range for a side of a box. Returns range(x), range(y)

    Args:
        box (tuple): Coordinates of the box in (x1, x2, y1, y2)

    Returns:
        Two values (int): x_range (int), y_range (int)

    """
    x_range = range(int(round(box[0])), int(round(box[2])))
    y_range = range(int(round(box[1])), int(round(box[3])))
    return x_range, y_range


def get_box_center(box):
    """
    Gets the center of a box. Returns x, y.

    Args:
        box (tuple): Coordinates of the box in (x1, x2, y1, y2)

    Returns:
        Two values (float): centerx (float), centerx (float)
    """
    centerx = round((box[0] + box[2]) / 2)
    centery = round((box[1] + box[3]) / 2)
    return centerx, centery


def filter_boxes(in_boxes, in_scores, _passed_boxes=[], _passed_scores=[]):
    """
    Filters overlapping boxes. Accepts two lists of equal length:
        1. a list of boxes (x1, x2, y1, y2)
        2. a list of scores for the boxes

    Solves ties by 1) highest score, or if
    those are tied, by 2) largest size. If the boxes are overlapping,
    but more than 20px apart, this is probably two cells and not overlapping
    boxes.

    Args:
        in_boxes (list): List of coordinates to filter,
            each item a tuple (x1, x2, y1, y2)
        in_scores (list): List of scores for each box
        _passed_boxes (list): Pass an empty list to this []
        _passed_scores (list): Pass an empty list to this []

    Returns:
        Two lists: passed_boxes (list of tuples), and pased_scores (list).
    """
    # This could be made faster using numpy and arrays
    # however, it runs fast enough for purposes of this program
    if not len(in_boxes) == len(in_scores):
        raise ValueError('The length of the box lists and score lists '
                         'must be equal.')
    if not len(in_boxes) > 1:
        return in_boxes, in_scores

    def inspot(box, test_box):
        box_x, box_y = extract_xyrange(box)
        test_box_x, test_box_y = extract_xyrange(test_box)

        intersect_x = set(box_x).intersection(test_box_x)
        intersect_y = set(box_y).intersection(test_box_y)

        centerx, centery = get_box_center(box)
        t_centerx, t_centery = get_box_center(test_box)

        overlap_bool = len(intersect_x) > 0 and len(intersect_y) > 0
        if overlap_bool:
            # If the centers are more than 20 px apart,
            # there is no tie to break. Likely two big boxes overlapping self.
            center_bool = (abs(centerx - t_centerx) < 20 and
                           abs(centery - t_centery) < 20)
            if center_bool:
                return True
        else:
            return False

    def untie(tied_boxes, tied_scores):  # 1. highest score, 2. biggest box.
        if len(tied_boxes) > 1:
            max_score = max(tied_scores)
            max_pos = [i for i, j in enumerate(tied_scores) if j == max_score]
            if len(max_pos) > 1:
                box_area = []
                for box in tied_boxes:
                    box_x, box_y = extract_xyrange(box)
                    area = ((max(box_x) - min(box_y) *
                            (max(box_y) - min(box_y))))
                    box_area.append(area)
                max_area = max(box_area)
                max_pos = [i for i, j in enumerate(box_area) if j == max_area]

            winner_box = tied_boxes[max_pos[0]]
            winner_score = tied_scores[max_pos[0]]
            return winner_box, winner_score
        else:
            return tied_boxes[0], tied_scores[0]

    test_box = in_boxes[0]
    tied_boxes = [test_box]
    tied_scores = [in_scores[0]]
    pass_forward_boxes = []
    pass_forward_scores = []

    if len(in_boxes) > 1:
        for box, score in zip(in_boxes[1:], in_scores[1:]):
            if inspot(box, test_box):
                tied_boxes.append(box)
                tied_scores.append(score)
            else:
                pass_forward_boxes.append(box)
                pass_forward_scores.append(score)

    passed_box, passed_score = untie(tied_boxes, tied_scores)
    _passed_boxes.append(passed_box)
    _passed_scores.append(passed_score)

    if not len(pass_forward_boxes) > 1:  # in case our last boxes are ties
        return _passed_boxes, _passed_scores
    if len(in_boxes) > 1:
        return filter_boxes(pass_forward_boxes, pass_forward_scores, _passed_boxes, _passed_scores)
    else:
        return _passed_boxes, _passed_scores
