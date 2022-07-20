import datetime
import math
import time
import gpxpy
import gpxpy.gpx
from numpy import NaN

# from common.SplinesArray import *
# import pandas as pd
from scipy.interpolate import interp1d, UnivariateSpline

SEPS = (' ', ',', '\t')


def read_csv(fpaths, time_cols=('DATE', 'TIME'), data_format="%m.%d.%yT%H:%M:%S,%f", onlyHead=False):
    """
    Reads magnetic CSV fies (*.csv, *.txt), which format can be

    ; param1: value1
    ; param2: value2
    ...
    ; paraml: valuel
    ; head1<sep>head2<sep>...<sep>headn
     val1<sep>val2<sep>...<sep>valn
     ...
     val1<sep>val2<sep>...<sep>valn

     where sep=(' ', ',', '\t').
     Regular CSV with these separators also accepted.
    """
    head = []
    data = []
    sep = None
    time_icols = []  # time columns indexes
    # points = {}  # {dateTime: (T, qmc, st} - dict

    for fpath in fpaths:
        with open(fpath, encoding='latin-1') as inf:
            lines = inf.readlines()
            # print(s)
            for i in range(len(lines)):
                if lines[i].find(';') != 0:
                    # находим разделитель
                    if sep is None:
                        c = [lines[i].count(s) for s in SEPS]
                        sep = SEPS[c.index(max(c))]
                        # print(sep)
                    # находим заголовок
                    if len(head) == 0:
                        if i - 1 > 0 and lines[i - 1].find(';') == 0:
                            head = [l for l in lines[i - 1][1:].replace('\n', '').split(sep) if l != '']
                        else:
                            head = [l for l in lines[i].replace('\n', '').split(sep) if l != '']
                            continue
                    if onlyHead: return head
                    # находим остальные элементы
                    elems = lines[i].replace('\n', '').split(sep)
                    # находим поле времени (если оно одно)
                    if len(time_cols) == 1:
                        time_icol = head.index(*time_cols)
                    # находим поля времени (если их два)
                    elif len(time_cols) > 1:
                        if len(time_icols) == 0:
                            time_icols = [head.index(l) for l in time_cols]
                            head[min(time_icols)] += '_' + head.pop(max(time_icols))
                        elems[min(time_icols)] += 'T' + elems.pop(max(time_icols))
                        time_icol = min(time_icols)  # после конкатенации столбец времени остается один (мин из двух)
                    # пересчитаем дату-время и запишем в отдельный столбец
                    try:
                        elems.append(datetime.datetime.strptime(elems[time_icol], data_format).timestamp())
                    except Exception as e:
                        print(f'Error {e}')
                        continue
                    data.append(elems)
                    # create a dictionary with unixdata as a key
                    # points.setdefault(elems[-1], (elems[0], elems[1], elems[2]))  # {dateTime: (T, qmc, st} - dict

    head.append('unix_time')
    # print(head)
    # print(*data, sep='\n')
    data = sorted(data, key=lambda x: x[-1])  # sort by unix_time
    # data.insert(0, head)
    return data

    # return sorted(points.items())  # [('a', 1), ('b', 2), ('c', 3)] - sorted list with tuples


def read_gpx(fpaths):
    """
    Reads gps files
    Returns interpolated functions
    """
    gpx_points = []
    x_set = set()
    # df = pd.DataFrame(columns=['TIME', 'LON', 'LAT', 'ALT'])
    k = 0
    for i, fpath in enumerate(fpaths):
        # print(f'Opening {i + 1}/{len(fpaths)} : {fpath}')

        with open(fpath, 'r', encoding="utf_8_sig") as inf:
            gpx = gpxpy.parse(inf)

        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    unix_time = (point.time - datetime.timedelta(hours=8)).timestamp()
                    # gpx_points.setdefault(unix_time, (point.longitude, point.latitude, point.elevation))
                    # df.loc[k] = [unix_time, point.longitude, point.latitude, point.elevation]
                    if unix_time not in x_set:
                        gpx_points.append([unix_time, point.longitude, point.latitude, point.elevation])
                        x_set.add(unix_time)
                        k += 1
    print(k)
    # df = df.set_index('TIME')
    # print(df)
    # lon_func = interp1d(df.index, df.LON, kind='cubic') # UnivariateSpline
    # lat_func = interp1d(df.index, df.LAT, kind='cubic')
    # alt_func = interp1d(df.index, df.ALT, kind='cubic')

    gpx_points = sorted(gpx_points, key=lambda x: x[0])
    x = [x[0] for x in gpx_points]
    lon = [x[1] for x in gpx_points]
    lat = [x[2] for x in gpx_points]
    alt = [x[3] for x in gpx_points]

    lon_func = interp1d(x, lon, kind='linear')
    lat_func = interp1d(x, lat, kind='linear')
    alt_func = interp1d(x, alt, kind='linear')

    # lon_func = interp1d(x, lon, kind='cubic')
    # lat_func = interp1d(x, lat, kind='cubic')
    # alt_func = interp1d(x, alt, kind='cubic')

    # lon_func = UnivariateSpline(line, lon)
    # lat_func = UnivariateSpline(line, lat)
    # alt_func = UnivariateSpline(line, alt)

    return lon_func, lat_func, alt_func
    # return


def gps_binding(inf_params, gpxs, res_path, sep='\t'):
    data = read_csv(*inf_params)

    # start_time = time.time()
    geom_func = read_gpx(gpxs)
    # print("--- %s seconds ---" % (time.time() - start_time))

    # print(*data[:10], sep='\n')
    # print(*gps[:10], sep='\n')

    with open(res_path, '+w') as ouf:
        ouf.write(sep.join(['FIELD', 'qmc', 'st', 'TIME', 'LON', 'LAT', 'ALT']) + '\n')
        for line in data:  # [344:400]
            try:
                new_geom = [geom_func[0](line[-1]), geom_func[1](line[-1]), geom_func[2](line[-1])]
                # data[i].extend(new_geom)
            except ValueError as e:
                new_geom = [0, 0, 0]
            # else:
            #     new_geom = [NaN, NaN, NaN]
            print(*line, *new_geom)
            # ouf.write(f'FIELD{sep}qmc{sep}st{sep}TIME{sep}LON{sep}LAT{sep}ALT\n')
            ouf.write(
                f'{int(line[0])/1000}{sep}{line[1]}{sep}{line[2]}{sep}{line[3]}{sep}{new_geom[0]}{sep}{new_geom[1]}{sep}{new_geom[2]}\n')
    with open(res_path) as ouf:
        if len(ouf.readlines()) > 0:
            return 1


if __name__ == '__main__':
    time_cols = ('DATE', 'TIME')
    data_format = "%m.%d.%yT%H:%M:%S,%f"
    sep = '\t'
    fpaths = [
        '/Users/ronya/PycharmProjects/TESTDATA/Aunakit/Aunakit_Data/Magn_Aunakit/20210721/Data/2021-07-21_02-42-06.txt',
        '/Users/ronya/PycharmProjects/TESTDATA/Aunakit/Aunakit_Data/Magn_Aunakit/20210721/Data/2021-07-21_04-29-56.txt']
    gpxs = ['/Users/ronya/PycharmProjects/TESTDATA/Aunakit/Aunakit_Data/Magn_Aunakit/20210721/LOG/00000001.BIN.gpx',
            '/Users/ronya/PycharmProjects/TESTDATA/Aunakit/Aunakit_Data/Magn_Aunakit/20210721/LOG/00000002.BIN.gpx']
    res_path = '/Users/ronya/PycharmProjects/OUTPUT/output1.txt'

    m = gps_binding((fpaths, time_cols, data_format), gpxs, res_path, sep)
