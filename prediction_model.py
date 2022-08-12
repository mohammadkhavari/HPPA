from random import randrange
import tensorflow as tf
from keras import layers, models, losses
from fetch_data import fetch_train_data, future_latency_shape, latency_history_input_shape, resource_history_input_shape
from sklearn.model_selection import train_test_split

def verify_gpu():
    # from tensorflow import keras
    # print(tf.reduce_sum(tf.random.normal([1000, 1000])))
    sess = tf.compat.v1.Session(config=tf.compat.v1.ConfigProto(log_device_placement=True))
    from tensorflow.python.client import device_lib
    print("\n\n-------\n\n", device_lib.list_local_devices())
    print("\n\n-------\n\n", tf.config.list_physical_devices('GPU'))
    # config = tf.config.set_logical_device_configuration(device_count = {'GPU': 1 , 'CPU': 1} ) 
    # sess = tf.Session(config=config) 
    # keras.backend.set_session(sess)

def create_model():
    # rh -> resource_history , lh-> latency_history, l -> (future)latency
    rh_input = layers.Input(shape=resource_history_input_shape())
    lh_input = layers.Input(shape=latency_history_input_shape())
    print(rh_input, lh_input)
    resource_history_model = create_rh_convolutional_layers(rh_input)
    latency_history_model = create_lh_convolutional_layers(lh_input)
    conv = layers.Concatenate(axis=1)([resource_history_model, latency_history_model])
    conv = layers.Flatten()(conv)
    dense = layers.Dense(64, activation='relu')(conv)
    dense = layers.Dropout(0.1)(dense)
    output = layers.Dense(units=1)(dense)
    model = models.Model(inputs=[rh_input, lh_input], outputs=output)
    model.summary()
    model.compile(optimizer='adam',
                loss=losses.mean_absolute_error,)

    tf.keras.utils.plot_model(
    model,
    to_file="model.png",
    show_shapes=False,
    show_dtype=False,
    show_layer_names=True,
    rankdir="TB",
    expand_nested=False,
    dpi=96,
    layer_range=None,
    show_layer_activations=False,)

    return model

def create_rh_convolutional_layers(rh_input):
    # filter, kernel should optimized
    filter, kernel_size, activation = resource_history_input_shape()[0], (3,3), "relu"
    model = layers.Conv2D(filter, kernel_size,activation = activation, padding='same')(rh_input)
    print(model.shape)
    model = layers.AveragePooling2D((2,2), padding='same',)(model)
    print(model.shape)
    model = layers.Dropout(0.1)(model)
    print(model.shape)
    model = layers.Conv2D(filter * 2, kernel_size, activation = activation, padding='same')(model)
    print(model.shape)
    model = layers.AveragePooling2D((2,2), padding='same')(model)
    print(model.shape)
    model = layers.Conv2D(filter * 2, kernel_size, activation = activation, padding='same')(model)
    model = layers.AveragePooling2D((2,1), padding='same')(model)
    model = layers.Dropout(0.1)(model)
    print(model.shape)
    model = layers.Reshape(model.shape[2:])(model)
    print(model.shape)
    return model

def create_lh_convolutional_layers(lh_input):
    # filter, kernel should optimized
    filter, kernel_size, activation = latency_history_input_shape()[0], 2, "relu"
    model = layers.Conv1D(filter, kernel_size, activation=activation)(lh_input)
    print(model.shape)
    model = layers.Conv1D(filters=filter*2, kernel_size=kernel_size, activation=activation)(model)
    print(model.shape)
    model = layers.Dropout(0.1)(model)
    print(model.shape)
    model = layers.MaxPooling1D(pool_size=2)(model)
    print(model.shape)
    return model

def train_model(model):
    (x_rh , x_lh), y_l = fetch_train_data(data_count=50, offset=0)
    train_x_rh, test_x_rh, train_x_lh, test_x_lh, train_y_l, test_y_l = train_test_split(x_rh, x_lh, y_l, test_size=0.2)
    tf.keras.backend.clear_session()
    print(f"memory usage {tf.config.experimental.get_memory_info('GPU:0')['current'] / 10 ** 6} MB")
    model.fit([train_x_rh, train_x_lh], train_y_l,
          batch_size=10,
          epochs=200,
          verbose=2,
          validation_data=([test_x_rh, test_x_lh], test_y_l),)

    print(model.evaluate([test_x_rh, test_x_lh], test_y_l))

    i = 50
    out = model.predict([x_rh[:i], x_lh[:i]], verbose=2)
    for i in range(0,50):
        print (out[i], y_l[i])
    

if __name__ == "__main__":
    verify_gpu()
    model = create_model()
    train_model(model)
