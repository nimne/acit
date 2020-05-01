def get_session():
    """
    Gets the modified tensorflow session.

    Returns:
        tensorflow.Session

    """
    import tensorflow as tf
    config = tf.compat.v1.ConfigProto()
    config.gpu_options.allow_growth = True
    return tf.compat.v1.Session(config=config)

def safe_load_model(model_path):
    """
    Wrapper function for keras_retinanet.load_model to account for different
    required arguments in different versions.

    Args:
        model_path: path to the .hd5 model file

    Returns:
        keras.models.model

    """
    from keras_retinanet import models
    try:  # For older versions of keras_retinanet
        model = models.load_model(model_path, backbone_name='resnet50', convert=True)
    except:
        model = models.load_model(model_path, backbone_name='resnet50')
    return model