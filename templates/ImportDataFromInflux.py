# https://influxdb-client.readthedocs.io/en/stable/index.html
# https://influxdb-client.readthedocs.io/en/stable/usage.html
# https://influxdb-client.readthedocs.io/en/latest/index.html
# https://github.com/influxdata/influxdb-client-python/tree/master/examples

"""
How to ingest large DataFrame by splitting into chunks.
"""
import datetime, os
from pytz import timezone
from influxdb_client.client.write_api import ASYNCHRONOUS, SYNCHRONOUS
from templates import config
from influxdb_client import (
    Point,
    InfluxDBClient,
    WriteOptions,
    WritePrecision,
)
import json
from influxdb_client.client.flux_table import FluxStructureEncoder
from influxdb_client.extras import pd
from influxdb_client.client import flux_table
import csv
import time
from collections import OrderedDict
from pathlib import Path
import re
from templates import launch_mode
"""
Configuration
"""

token = "CjNhQHje2pEPhEkv3YrZQPAVnRtGm4sfBIN7KDJuYZderM3NIqStIzWprARxcc5XgiMv_WbWSwKzGti_hlxfsw=="
org = "cadis_framatome"
bucket = "Pumps"
"""
# Define a few variables with the name of your bucket, organization, and token.
url = "http://localhost:8086"
token = "d-SqvnIj7DD0QC1pBszH2jqbWtqZ7gWYxx6Q6Rix8ykR1hu0Xd6NpK4gbsO3W-hJlKblMUkX_e2c5p54-4w0oA=="
org = "myOrg"  # "cadis_framatome"
bucket = "cadis_bucket"
measurement = "cadis_table"
data_ingest = "batch"  # or ingest_df
"""

timecolumn = "Date_Time"
batchsize = 1
delimiter = ";"
decimal = ","
timeformat = "%Y-%m-%d %H:%M:%S.%f"
datatimezone = "UTC"  # 'Europe/Berlin' #
datetime_from_csv_file = False

url = launch_mode.url


# data=pd.read_csv(r"D:/MG/InfluxDatas/Pumps/Pump_1/Process_Parameters_20220708_211000.csv", sep=";", decimal=",")
def status_to_emoji(input):
    thing = int(input)
    if thing == 0:
        return "◯"
        # return "🔵"
    if thing == 1:
        return "🟢"
    if thing == 2:
        return "🟡"
    if thing == 3:
        return "🟠"
    if thing == 4:
        return "🔴"
    return "◯"

def convert_df_row_to_datapoint(row, measurement, fieldcolumns, tagcolumns,add_tags = {}):
    # date_time_row_ = datetime.datetime.now() - datetime.timedelta( hours=1 * row_idx)  # .strftime (timeformat)#[:-6]
    # date_time_row_ =
    # date_time_row = date_time_row_.strftime(timeformat)  # [:-6]
    # print(date_time_row)
    # row[timecolumn] = date_time_row

    try:
        datetime_naive = datetime.datetime.strptime(row[timecolumn], timeformat)
    except:
        row_date_time = str(row[timecolumn]) + ".000"
        datetime_naive = datetime.datetime.strptime(row_date_time, timeformat)

    if datetime_naive.tzinfo is None:
        datetime_local = timezone(datatimezone).localize(datetime_naive)
    else:
        datetime_local = datetime_naive
    # print (datetime_local)
    # datetime_local = datetime_naive
    # print (datetime_local)
    timestamp = unix_time_millis(datetime_local) * 1000000  # in nanoseconds
    # timestamp = unix_time_millis(datetime_local, datatimezone) * 1000000  # in nanoseconds

    fields = create_fields(fieldcolumns, row)
    tags = create_tags(tagcolumns, row)
    tags=tags | add_tags

    dictionary = {
        "measurement": measurement,
        "tags": tags,
        "fields": fields,
        "time": timestamp,
    }

    point = Point.from_dict(dictionary, WritePrecision.NS)
    line_protocol = point.to_line_protocol()
    return line_protocol, point, dictionary


# print(epoch)
def unix_time_millis(dt, datatimezone="Europe/Berlin"):
    # logging.info('unix_time_millis is started')
    epoch_naive = datetime.datetime.utcfromtimestamp(0)
    epoch = timezone(datatimezone).localize(epoch_naive)
    return int((dt - epoch).total_seconds() * 1000)


## Check data type
def isfloat(value):
    # logging.info('isfloat is started')
    try:
        float(value)
        return True
    except:
        return False


def isbool(value):
    # logging.info('isbool is started')
    try:
        return value.lower() in ("true", "false")
    except:
        return False


def str2bool(value):
    # logging.info('str2bool is started')
    return value.lower() == "true"


def isinteger(value):
    # logging.info('isinteger is started')
    try:
        if float(value).is_integer():
            return True
        else:
            return False
    except:
        return False


def create_fields(fieldcolumns, row):
    # logging.info('create_fields is started')
    fields = {}

    for f in fieldcolumns:
        # print(f, row[f])
        v = 0
        if f in row and row[f] != None:
            if "," in str(row[f]):
                value = row[f].replace(",", ".")
            elif "NaN" in str(row[f]) or "nan" in str(row[f]) or "NAN" in str(row[f]):
                value = 0
            else:
                value = row[f]
            if isfloat(value):
                v = float(value)
            elif isbool(value):
                v = str2bool(value)
            elif isinteger(value):
                v = int(value)
            elif isinstance(value, str):
                v = str(value)
            else:
                v = str(row[f])
            # if '%' in f or 'µm' in f or '°C' in f:
            #     f = f[:-2]
            if f == "FileId":
                v = "L" + str(row[f])
            fields[f] = v
    return fields


def create_tags(tagcolumns, row):
    # logging.info('create_tags is started')
    tags = {}
    for t in tagcolumns:
        v = 0
        if t in row:
            v = row[t]
        if t == "Asset":
            pass
            # v = 'AssetName'
        tags[t] = v
    return tags


def get_info_csv_file(csv_file):
    df_all = pd.read_csv(csv_file, sep=delimiter, decimal=decimal, low_memory=False)
    df_all["Date_Time"] = pd.to_datetime(
        df_all["Date_Time"], format="%Y-%m-%d %H:%M:%S.%f", errors="ignore"
    )
    df_all.fillna(0, inplace=True)
    # print(df_all.describe())

    LabelNames = []
    PredictorNames = []
    for feat in df_all.columns:
        if feat != "Date_Time":
            if df_all[feat].dtype == "object":  # or "-Status" in feat:
                LabelNames.append(feat)
            else:
                PredictorNames.append(feat)
    fieldcolumns = PredictorNames
    tagcolumns = LabelNames
    observations = df_all.shape[0]

    if observations > 1000:
        batchsize = 1000
    elif observations > 500:
        batchsize = 500
    elif observations > 100:
        batchsize = 100
    elif observations > 50:
        batchsize = 50
    elif observations > 10:
        batchsize = 10
    elif observations > 5:
        batchsize = 5
    else:
        batchsize = 1
    # print ('observations: ', observations, 'batchsize: ', batchsize)
    # print ("LabelNames: ", LabelNames)
    # print ("PredictorNames: ", PredictorNames)

    return df_all, fieldcolumns, tagcolumns, batchsize


def do_bucket(bucket_name, function="delete"):
    with InfluxDBClient(url=url, token=token) as client:
        buckets_api = client.buckets_api()

        """
        List all Buckets befpre
        """
        print(f"\n------- List -------\n")
        buckets = buckets_api.find_buckets().buckets
        print(
            "\n".join(
                [
                    f" ---\n ID: {bucket.id}\n Name: {bucket.name}\n Retention: {bucket.retention_rules}"
                    for bucket in buckets
                ]
            )
        )
        print("---")
        bucket_list = []
        for bucket_ in buckets:
            bucket_list.append(bucket_.name)

        if function == "create":
            """
            Create Bucket with retention policy set to 3600 seconds and name "bucket-by-python"
            """
            if bucket_name not in bucket_list:
                print(f"------- Create -------\n")
                # retention_rules = BucketRetentionRules(type="expire", every_seconds=3600)
                created_bucket = buckets_api.create_bucket(
                    bucket_name=bucket_name,
                    # retention_rules=retention_rules,
                    org=org,
                )

                """
                Update Bucket
                """
                print(f"------- Update -------\n")
                created_bucket.description = "Update description"
                # created_bucket = buckets_api.update_bucket (bucket=created_bucket)
                print(created_bucket)

        if function == "delete":
            """
            Delete previously created bucket
            """
            print(f"------- Delete -------\n")
            bucket = buckets_api.find_bucket_by_name(bucket_name)
            if bucket != None and bucket_name in bucket_list:
                buckets_api.delete_bucket(bucket)
                print(f" successfully deleted bucket: {bucket_name}")

        """
        List all Buckets after
        """
        print(f"\n------- List -------\n")
        buckets = buckets_api.find_buckets().buckets
        print(
            "\n".join(
                [
                    f" ---\n ID: {bucket.id}\n Name: {bucket.name}\n Retention: {bucket.retention_rules}"
                    for bucket in buckets
                ]
            )
        )
        print("---")


class InfluxQueryBuilder:
    def __init__(self, bucket):
        self.__bucket = bucket
        self.__function_chain = {"range": None, "filters": None}
        self.__fields = []

    def range(self, start="0", stop=None):
        if stop is None:
            self.__function_chain["range"] = f"range(start: {start})"
        else:
            self.__function_chain["range"] = f"range(start: {start}, stop: {stop})"
        return self

    def filter(self, expression, param_name="r"):
        """
        Will keep appending filter functions on each call
        """
        query_string = f"filter(fn: ({param_name}) => {expression})"
        if self.__function_chain["filters"] is None:
            self.__function_chain["filters"] = [query_string]
        else:
            self.__function_chain["filters"].append(query_string)
        return self

    def field(self, field):
        self.__fields.append(f'r["_field"] == "{field}"')
        return self

    def measurement(self, measurement):
        """
        Call measurement before field
        """
        self.filter(f'r["_measurement"] == "{measurement}"')
        return self

    def build(self):
        """
        Build the flux query
        """
        if self.__fields:
            self.filter(" or ".join(self.__fields))
        query = f'from(bucket: "{self.__bucket}")'
        for k, v in self.__function_chain.items():
            if v is not None:
                if type(v) is list:
                    for item in v:
                        query += f"\n|> {item}"
                else:
                    query += f"\n|> {v}"
        return query


def query_bucket_measurement(
        bucket_name, measurement_name, from_date, to_date, query_method="data_frame"):
    """
    """
    t0 = datetime.datetime.now()
    TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"
    # datetime.datetime.strftime (from_date, TIMESTAMP_FORMAT)
    # from_date = 0; to_date = 0
    if (
            (from_date == 0 and to_date == 0)
            or (from_date == "0" and to_date == "0")
            or (from_date == None and to_date == None)
    ):
        from_date = 0
        to_date = datetime.datetime.now()
        to_date = datetime.datetime.strftime(to_date, TIMESTAMP_FORMAT)

    if from_date != "0" and from_date != 0 and from_date != None:
        if len(from_date) <= 10:
            from_date = from_date + "T00:00:00.000000"
    if to_date != "0" and to_date != 0 and to_date != None:
        if len(to_date) <= 10:
            to_date = to_date + "T00:00:00.000000"
    try:
        from_date = datetime.datetime.strftime(from_date, TIMESTAMP_FORMAT)
    except:
        from_date = from_date

    try:
        to_date = datetime.datetime.strftime(to_date, TIMESTAMP_FORMAT)
    except:
        to_date = to_date

    if from_date != 0 and from_date != None:
        from_date = from_date + "Z"
    else:
        from_date = str(0)
    to_date = to_date + "Z"

    with InfluxDBClient(url=url, token=token, org=org, timeout=100_000) as client:

        query = (
            f'from(bucket:"{bucket_name}")'
            f"|> range(start: {from_date}, stop: {to_date})"
            f'|> filter(fn: (r) => r._measurement == "{measurement_name}")'
            '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")')

        # print(query)
        if query_method != "data_frame":
            result = client.query_api().query(org=org, query=query)
            # print(result)

            # print(
            #     result[2].records[5].get_measurement()
            # )  # get_measurement(): Returns the measurement name record
            # print(
            #     result[2].records[5].get_field()
            # )  # get_field(): Returns the field name.
            # print(
            #     result[2].records[5].get_value()
            # )  # get_value(): Returns the actual field value.
            # print(
            #     result[2].records[5].values
            # )  # values: Returns a map of column values. --> dict
            # print(
            #     result[2].records[5].values.keys()
            # )  # values: Returns a map of column values.
            # print(
            #     result[2].records[5].values.values()
            # )  # values: Returns a map of column values.
            # # values.get("<your tag>"): Returns a value from the record for given column.
            # print(
            #     result[2].records[5].get_time()
            # )  # get_time(): Returns the time of the record.
            # print(
            #     result[2].records[5].get_start()
            # )  # get_start(): Returns the inclusive lower time bound of all records in the current table.
            # print(
            #     result[2].records[5].get_stop()
            # )  # get_stop(): Returns the exclusive upper time bound of all records in the current table.

            results = []
            for table in result:
                for record in table.records:
                    results.append((record.values.keys(), record.values.values()))
                    # results.append((record.get_field(), record.get_value()))
            # print(results)
            result_df = results
        else:
            result_df = client.query_api().query_data_frame(org=org, query=query)
    if result_df.shape[0] > 1 and result_df.shape[1] > 1:

        result_df["_time"] = pd.to_datetime(
            result_df["_time"], format="%Y-%m-%dT%H:%M:%S.%f", errors="ignore"
        )
        result_df.sort_values(
            by="_time", axis=0, inplace=True, ascending=True
        )  # Sortierung nach Date_Time
        result_df.index = range(len(result_df.index))
        if "Date_Time" not in result_df.columns:
            #result_df.insert(0, "Date_Time", result_df._time.values)
            result_df=pd.concat([pd.DataFrame(result_df._time.values,columns=['Date_Time']),result_df],axis=1)
            result_df.drop("_time", axis=1, inplace=True)

        result_df["Date_Time"] = result_df["Date_Time"] + datetime.timedelta(hours=-1)

        del_feat_list = ["result", "table", "_start", "_stop", "_time", "_measurement"]
        for feat in del_feat_list:
            if feat in result_df.columns:
                result_df.drop(feat, axis=1, inplace=True)

        # print(result_df.columns.to_list())

    t1 = datetime.datetime.now()
    LabelNames = []
    PredictorNames = []
    for feat in result_df.columns:
        if feat != "Date_Time":
            if result_df[feat].dtype == "object":
                LabelNames.append(feat)
            else:
                PredictorNames.append(feat)
    # print("LabelNames", LabelNames)
    # print("PredictorNames", PredictorNames)
    fieldList, tagList = PredictorNames, LabelNames
    return result_df, fieldList, tagList


def import_csv_row_to_influxdb(
        csv_file, measurement, fieldcolumns, tagcolumns, twait, datetime_from_csv_file=False
):
    inputfile = open(csv_file, "r")
    datapoints = []
    count = 0
    with inputfile as csvfile:
        reader = csv.DictReader(csvfile, delimiter=delimiter)
        for row_idx, row in enumerate(reader):
            line_protocol, datapoint, dictionary = convert_df_row_to_datapoint(
                row, measurement, fieldcolumns, tagcolumns, row_idx
            )

            client = InfluxDBClient(url=url, token=token, org=org)
            write_api = client.write_api(write_options=ASYNCHRONOUS)
            # write_api = client.write_api(write_options=WriteOptions(batch_size=500, flush_interval=10_000, jitter_interval=2_000, retry_interval=5_000))
            write_api.write(bucket=bucket, org=org, record=line_protocol)
            client.close()

            datapoints.append(line_protocol)
            count += 1

    return datapoints


def parse_csv_file(
        csv_file, measurement, fieldcolumns, tagcolumns, twait, add_tags, datetime_from_csv_file=False
):
    inputfile = open(csv_file, "r")
    datapoints = []
    count = 0
    with inputfile as csvfile:
        reader = csv.DictReader(csvfile, delimiter=delimiter)
        for row in reader:
            line_protocol, datapoint, dictionary = convert_df_row_to_datapoint(
                row,
                measurement,
                fieldcolumns,
                tagcolumns,
              add_tags,
            )
            # if count >= 0 and twait >= 1:
            #     print(count)
            #     print(dictionary)
            #     print(datapoint)
            #     print(line_protocol)
            #     print()

            datapoints.append(datapoint)
            count += 1

            #  if twait > 0:
            #     time.sleep(twait)
    return datapoints


def parse_row(
        row: OrderedDict,
        measurement,
        fieldcolumns,
        tagcolumns,
        datetime_from_csv_file=False,
):
    # print(row)
    line_protocol, datapoint, dictionary = convert_df_row_to_datapoint(
        row,
        measurement,
        fieldcolumns,
        tagcolumns,
        datetime_from_csv_file=datetime_from_csv_file,
    )
    return datapoint


def write_bucket_measurement(
        csv_file,
        bucket="cadis_bucket",
        measurement="",
        data_ingest="line",
        twait=1,
        repeat_while=False,add_tags= {}
):
    t0 = datetime.datetime.now()

    if measurement == None or measurement == "":
        measurement = csv_file.split(os.sep)[-1].split("_")[0]
    # read csv_file
    data_frame, fieldcolumns, tagcolumns, batchsize = get_info_csv_file(csv_file)

    fieldcolumns.extend(tagcolumns)
    tagcolumns = []

    # ingest data_frame

    if data_ingest == "line":
        print("data_ingest: ", data_ingest)
        while True:
            datapoints = import_csv_row_to_influxdb(
                csv_file,
                measurement,
                fieldcolumns,
                tagcolumns,
                twait,
                datetime_from_csv_file=False,
            )
            if repeat_while == False:
                break

    if data_ingest == "batch":
        print("data_ingest: ", data_ingest)
        datapoints = parse_csv_file(
            csv_file,
            measurement,
            fieldcolumns,
            tagcolumns,
            twait,
            add_tags,
            datetime_from_csv_file=True,
        )

        with InfluxDBClient(
                url=url, token=token, org=org
        ) as client:  # problem if columns length can change
            with client.write_api(
                    write_options=WriteOptions(batch_size=50_000, flush_interval=10_000)
            ) as write_api:
                write_api.write(bucket=bucket, record=datapoints)

    if data_ingest == "df":
        print("data_ingest: ", data_ingest)
        with InfluxDBClient(
                url=url, token=token, org=org
        ) as client:  # problem if columns length can change
            data_frame.index = data_frame.Date_Time
            data_frame.drop("Date_Time", axis=1, inplace=True)
            if "Date_Time" in tagcolumns:
                tagcolumns.remove("Date_Time")
            write_api = client.write_api(write_options=SYNCHRONOUS)
            write_api.write(
                bucket=bucket,
                record=data_frame,
                data_frame_measurement_name=measurement,
                data_frame_tag_columns=tagcolumns,
            )

            # print(bucket, measurement, tagcolumns, data_frame.columns.to_list())

            """
            How to check the influxdb2 gui --> http://localhost:8086/
            from(bucket:"Bucket")
                |> range(start: 0)
                |> filter(fn: (r) => r._measurement == "Measurement")
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")

            Pie chart
            from(bucket: "cadis_bucket")
                  |> range(start: 0)
                  |> filter(fn: (r) => r["_measurement"] == "CNT_SUES")
                  |> filter(fn: (r) => r["_field"] =~ /A2/ and r["_field"] =~ /-Status/ and r["_field"] !~ /_/)
                  |> duplicate(column: "_value", as: "new_column")
                  |> group(columns: ["new_column"])
                  |> count()
                  |> rename(columns: {new_column: "Status", _value: "Count"})

            histogram
            from(bucket: "${bucket_list}")
                  |> range(start: 2010-05-22T23:30:00Z)
                  |> filter(fn: (r) => r["_measurement"] =~ /${table_list}/ and r["_field"] =~ /Equipment/ and r["_field"] =~ /-Status/)
                  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
                  |> keep(columns: ["Equipment-Status"])
            """
    t1 = datetime.datetime.now()
    print("data ingesting duration: ", t1 - t0)

def get_measurement_list(url,token,org,bucket) :
    with InfluxDBClient(url=url, token=token, org=org, timeout=100_000) as client:
        query = (f'import "influxdata/influxdb/schema"'\
                'schema.measurements(bucket: "'+bucket+ '")')
        result = client.query_api().query(org=org, query=query)
        client.close()
    L=[]
    for el in result[0].records :
        L.append(el.values["_value"])
    return L

def get_bucket_list(url,token,org) :
    with InfluxDBClient(url=url, token=token, org=org, timeout=100_000) as client:
        query = (f'buckets()')
        result = client.query_api().query(org=org, query=query)
        client.close()
    L=[]
    for el in  result[0].records:
        L.append(el.values["name"])
    L.remove("_monitoring")
    L.remove("_tasks")
    return L

def useabledf(result_df):
    result_df["_time"] = pd.to_datetime(
        result_df["_time"], format="%Y-%m-%dT%H:%M:%S.%f", errors="ignore"
    )
    result_df.sort_values(
        by="_time", axis=0, inplace=True, ascending=True
    )  # Sortierung nach Date_Time
    result_df.index = range(len(result_df.index))
    if "Date_Time" not in result_df.columns:
        # result_df.insert(0, "Date_Time", result_df._time.values)
        result_df = pd.concat([pd.DataFrame(result_df._time.values, columns=['Date_Time']), result_df], axis=1)
        result_df.drop("_time", axis=1, inplace=True)

    result_df["Date_Time"] = result_df["Date_Time"] + datetime.timedelta(hours=-1)

    del_feat_list = ["result", "table", "_start", "_stop", "_time", "_measurement"]
    for feat in del_feat_list:
        if feat in result_df.columns:
            result_df.drop(feat, axis=1, inplace=True)
    return(result_df)

def get_channel_list(url,token,org,bucket,measurement, sep = "_") :
    """
    Only get channel with status
    """
    with InfluxDBClient(url=url, token=token, org=org, timeout=100_000) as client:
        query = (f'from(bucket:"{bucket}")'
                 f"|> range(start: 0)"
                 f'|> filter(fn: (r) => r._measurement == "{measurement}")'
                 '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")'
                 '|> limit(n : 1)')
        df = useabledf(client.query_api().query_data_frame(org=org, query=query))
        client.close()
    liste=list(df.columns)
    liste.remove("Date_Time")
    liste = [x for x in liste if x.endswith("-Status")]
    L=[]
    for el in liste :
        L.append(re.split(r'_|-',el)[0])
    return list(set(L))


def get_main_stuff(url,token,org,bucket,measurement = None,sep='_') :
    """
    Give the main info from a measurement (last update, channels, param by channels, parameters, 3 last status).
    :param url:
    :param token:
    :param org:
    :param bucket:
    :param measurement:
    :param sep:
    :return:
    """
    with InfluxDBClient(url=url, token=token, org=org, timeout=100_000) as client:
        query = (f'from(bucket:"{bucket}")'
                 f"|> range(start: 0)"
                 f'|> filter(fn: (r) => r._measurement == "{measurement}")'
                 '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")'
                 '|> sort(columns : ["_time"], desc : true)'
                 '|> limit(n : 3)')
        df = useabledf(client.query_api().query_data_frame(org=org, query=query))
        client.close()
    liste = list(df.columns)
    lastup=df["Date_Time"].max()
    liste.remove("Date_Time")
    liste = [x for x in liste if x.endswith("-Status")]
    L = []
    for el in liste:
        L.append(re.split(r'_|-', el)[0])
    channels=list(set(L))
    dicochan={}
    for channel in channels :
        lis = [x for x in liste if x.startswith(channel)]
        L = []
        for el in liste:
            u = re.split(r'_|-', el)

            if len(u) > 1:
                L.append(el[len(channel) + 1:len(el)])
            else:
                L.append(u[0])
        dicochan[channel]=list(set(L))
    param = []
    for el in channels:
        param = param + dicochan[el]
    param = list(set(L))
    param.sort()
    last_states=[status_to_emoji(df["Equipment-Status"][i]) for i in range(3)]
    last_sev=df["Equipment-Sev"][0]
    dico={}
    for chan in channels :
        dico[chan]=[df[chan + "-Status"][0],df[chan + '-Sev'][0]]
    return lastup,channels,dicochan,param,last_states,last_sev,dico

def get_features_channel(url,token,org,bucket,measurement,channel,sep='_') :
    """
    Only work with datas "Channel_features".
    """
    with InfluxDBClient(url=url, token=token, org=org, timeout=100_000) as client:
        query = (f'from(bucket:"{bucket}")'
                 f"|> range(start: 0)"
                 f'|> filter(fn: (r) => r._measurement == "{measurement}")'
                 '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")'
                 '|> sort(columns : ["_time"], desc : true)'
                 '|> limit(n : 1)')
        df = useabledf(client.query_api().query_data_frame(org=org, query=query))
        client.close()
    liste = list(df.columns)
    if channel is not None :
        liste = [x for x in liste if x.startswith(channel)]
    L=[]
    for el in liste:
        u = re.split(r'_|-',el)

        if len(u) > 1 :
            L.append(el[len(channel)+1:len(el)])
        else :
            L.append(u[0])
    return list(set(L))

def get_last_update(url,token,org,bucket,measurement,sep='_') :
    """
    Only work with datas "Channel_features".
    """
    with InfluxDBClient(url=url, token=token, org=org, timeout=100_000) as client:
        query = (f'from(bucket:"{bucket}")'
                 f"|> range(start: 0)"
                 f'|> filter(fn: (r) => r._measurement == "{measurement}")'
                 '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")'
                 '|> sort(columns : ["_time"], desc : true)'
                 '|> limit(n : 1)')
        df = useabledf(client.query_api().query_data_frame(org=org, query=query))
        client.close()
    return(df["Date_Time"].max())


if __name__ == "__main__":
    r"""
    main_path=r"D:/MG/InfluxDatas/Pompes/pompe 1/"
    files=[f for f in os.listdir(main_path + "Trend/")]
    for f in files :
        write_bucket_measurement(main_path + "Trend/"+ f,bucket ="Pompes",measurement = "pompe 1",data_ingest='batch',add_tags = {"data_type" : "trend"})

    #write_bucket_measurement(r"D:/MG/InfluxDatas/Pump_FeatureTable_Clean.csv", bucket="Pompes", measurement="Pompe 2", data_ingest='batch')
    do_bucket("OL3S", function="create")
    do_bucket("RCPS", function="create")
    write_bucket_measurement(r"D:/MG/InfluxDatas/OL3_FeatureTable_Clean.csv",bucket ="OL3S",measurement = "OL3 - Asset 1",data_ingest='batch')
    write_bucket_measurement(r"D:/MG/InfluxDatas/RCP_FeatureTable_Clean.csv", bucket="RCPS", measurement="RCP - Asset 1",
                             data_ingest='batch')
    df,_,_=query_bucket_measurement('Pompes',"pompe 1", from_date=None,to_date=None)
    print(get_channel_list(url,token,org,"Pompes","pompe 1"))
    print(get_features_channel(url,token,org,"Pompes","pompe 1","K1"))
    #get_measurement_list(url, token, org, "Pompes")

    do_bucket("OL3S", function="create")
    do_bucket("RCPS", function="create")
    do_bucket("Pumps", function="create")
    do_bucket("SUES", function="create")
    write_bucket_measurement(r"..\data\InfluxDatas\RCP_FeatureTable_Clean.csv", bucket="RCPS",
                             measurement="RCP - Asset 1",
                             data_ingest='batch')
    write_bucket_measurement(r"..\data\InfluxDatas\Pump_FeatureTable_Clean.csv", bucket="Pumps", measurement="pump 1",
                             data_ingest='batch')
    """
    def initdata() :
        do_bucket("OL3S", function="create")
        do_bucket("RCPS", function="create")
        do_bucket("Pumps", function="create")
        do_bucket("SUES", function="create")
        write_bucket_measurement(r"..\data\InfluxDatas\RCP_FeatureTable_Clean.csv", bucket="RCPS",
                                 measurement="RCP - Asset 1",
                                 data_ingest='batch')
        write_bucket_measurement(r"..\data\InfluxDatas\OL3S_FeatureTable_Clean.csv", bucket="OL3S",
                                 measurement="OL3S - Asset 1",
                                 data_ingest='batch')
        write_bucket_measurement(r"..\data\InfluxDatas\Pump_FeatureTable_Clean.csv", bucket="Pumps", measurement="pump 1",
                                 data_ingest='batch')
        write_bucket_measurement(r"..\data\InfluxDatas\SUES_FeatureTable_Clean.csv",
                                 bucket="SUES", measurement="sues 1",
                                 data_ingest='batch')
    #write_bucket_measurement(r"C:/BDA/CadisMockup/data/InfluxDatas/RCP2_FeatureTable_Clean.csv", bucket="RCPS", measurement="RCP - Asset 2", data_ingest='batch')

