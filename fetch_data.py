from sqlalchemy import create_engine
from monitoring.models import Service
from sqlalchemy.orm import Session
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

SERVICES_COUNT = 8
HISTORY_WINDOW = 5
SERVICE_RESOURCE_FEATURES = 3 # cpu, ram, replica + (pre-launch validation -> time_serie)

engine = create_engine(
    "postgresql://postgres:password@localhost:5432/metrics")

def fetch_train_data(data_count = 20, offset = 5):
    """
        fetch train data inputs, output from metrics db -> (X_RH, X_LH), Y_L

        NOTE: considering sliding window on time_series and
        train data count we need (data_count + HISTORY_WINDOW - 1) + 1(*) time_series
        [[1], [2], [3], [4], [5], [6(*)]] -> [[1,2,3], [2,3,4], [3,4,5]]
        * or + 1 is only for fetching last data Y_L (future latency)
    """
    service_records = []
    time_series_count = data_count + HISTORY_WINDOW
    with Session(engine) as session:
        query = session.query(Service).\
            order_by(Service.time_serie, Service.name).\
            limit(time_series_count * SERVICES_COUNT).\
            offset(offset * SERVICES_COUNT)
        service_records = query.all()
    X_RH, X_LH = extract_input_data(service_records, data_count, time_series_count)
    Y_L = extract_output_data(service_records, data_count, time_series_count)
    return (X_RH, X_LH), Y_L

def extract_input_data(records, data_count, time_series_count):
    X_RH = extract_resource_history(records, data_count, time_series_count)
    X_LH = extract_latency_histroy(records, data_count, time_series_count)
    assert(X_RH.shape == (data_count, HISTORY_WINDOW, SERVICES_COUNT, SERVICE_RESOURCE_FEATURES))
    assert(X_LH.shape == (data_count, HISTORY_WINDOW))

    return X_RH, X_LH

def extract_output_data(records, data_count, time_series_count):
    Y_L = extract_future_latency(records, data_count, time_series_count)

    assert(Y_L.shape == (data_count, 1))

    return Y_L    

# X_RH
def extract_resource_history(records, data_count, time_series_count):
    # add record.time_serie and SERVICE_RESOURCE_FEATURES to check validity by time_series 
    raw_records_data = np.array([[record.memory, record.cpu, record.replicas] for record in records])
    time_series_data = raw_records_data.reshape((time_series_count, SERVICES_COUNT, SERVICE_RESOURCE_FEATURES))[:-1] # delete last element that is only for Y_L 
    X_RH = sliding_window_view(time_series_data, (HISTORY_WINDOW, SERVICES_COUNT, SERVICE_RESOURCE_FEATURES)).\
        reshape(data_count, HISTORY_WINDOW, SERVICES_COUNT, SERVICE_RESOURCE_FEATURES)
    return X_RH
    
# X_LH
def extract_latency_histroy(records, data_count, time_series_count):
    # uncomment to check validity by time_series
    # time_series_data = np.array([[record.time_serie, record.latency] for record in records if record.name == "frontend"])[:-1] # delete last element that is only for Y_L 
    # X_LH = sliding_window_view(time_series_data, (HISTORY_WINDOW, 2))
    
    time_series_data = np.array([record.latency for record in records if record.name == "frontend"])[:-1] # delete last element that is only for Y_L 
    X_LH = sliding_window_view(time_series_data, HISTORY_WINDOW)
    return X_LH

# Y_L
def extract_future_latency(records, data_count, time_series_count):
    # uncomment to check validity by time_series
    time_series_data = np.array([record.latency for record in records if record.name == "frontend"])
    Y_L = time_series_data[HISTORY_WINDOW:].reshape(data_count, 1)
    return Y_L

print(fetch_train_data(4, 10))