import datetime
import math
import os
import time
import gpxpy
import gpxpy.gpx
from numpy import NaN

# from common.SplinesArray import *
# import pandas as pd
from scipy.interpolate import interp1d, UnivariateSpline

ACCEPTED_TXT_SEPS = {'Space': ' ',
                     'Comma': ',',
                     'Tab': '\t',
                     'Semicolon': ';'}

class GPSBuilder:

    def read_csv(self, fpaths, sep=' ', time_cols=('DATE', 'TIME'), data_format="%m.%d.%yT%H:%M:%S,%f", onlySep=False, onlyHead=False, onlyTHead=False):
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

         where sep=(' ', ',', '\t', ';').
         Regular CSV with these separators also accepted.
        """
        head = []
        data = []
        time_icols = []  # time columns indexes
        found_sep = None

        for fpath in fpaths:
            with open(fpath, encoding='latin-1') as inf:
                lines = inf.readlines()
                for i in range(len(lines)):
                    if not lines[i].startswith(';'):
                        # находим разделитель (предполагаемый)
                        if onlySep and found_sep is None:
                            mc = {}
                            for sep in ACCEPTED_TXT_SEPS.values():
                                a = [l for l in lines[i].replace('\n', '').split(sep) if l != '']
                                mc.setdefault(len(a), sep)
                            # print(mc)
                            found_sep = mc[max(mc.keys())]
                            return found_sep
                        # находим заголовок
                        if len(head) == 0:
                            if lines[i-1].startswith(';'):
                                head = [l for l in lines[i - 1][1:].replace('\n', '').split(sep) if l != '']
                            if set([l.isdigit() for l in lines[i].replace('\n', '').split(sep) if l != '']) == {False}:
                                head = [l for l in lines[i].replace('\n', '').split(sep) if l != '']
                                continue
                        if onlyHead:  # returns head from the first file
                            return head
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
                                head[min(time_icols)] = 'TIME'
                            elems[min(time_icols)] += 'T' + elems.pop(max(time_icols))
                            time_icol = min(time_icols)  # после конкатенации столбец времени остается один (мин из двух)
                        if onlyTHead: return head
                        # пересчитаем дату-время и запишем в отдельный столбец
                        try:
                            elems.append(datetime.datetime.strptime(elems[time_icol], data_format).timestamp())
                            if 'unix_time' not in head:
                                head.append('unix_time')
                        except Exception as e:
                            print(f'Error {e} в файле {fpath}')
                            continue
                        data.append(elems)

        data = sorted(data, key=lambda x: x[-1])  # sort by unix_time
        return head, data

    def get_gps_points(self, head, data, geom_cols=('LON', 'LAT', 'ALT')):
        cols = ['unix_time'] + list(geom_cols)
        if not all(item in head for item in cols):
            return -1, 'Данные геометрии не найдены в gps файлах', []
        else:
            icols = [head.index(l) for l in cols]
            gps_points = []
            for line in data:
                new_line = []
                for i in icols:
                    new_line.append(line[i])
                gps_points.append(new_line)
            gps_points = sorted(gps_points, key=lambda x: x[0])
            return gps_points

    def read_gpx(self, fpaths):
        """
        Reads gps files
        Returns interpolated functions
        """
        gpx_data = []
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
                        # gpx_data.setdefault(unix_time, (point.longitude, point.latitude, point.elevation))
                        # df.loc[k] = [unix_time, point.longitude, point.latitude, point.elevation]
                        if unix_time not in x_set:
                            gpx_data.append([unix_time, point.longitude, point.latitude, point.elevation])
                            x_set.add(unix_time)
                            k += 1
        # print(k)
        gpx_data = sorted(gpx_data, key=lambda x: x[0])
        return gpx_data

    def get_interpolated_func(self, gpx_data):
        x = [x[0] for x in gpx_data]
        lon = [x[1] for x in gpx_data]
        lat = [x[2] for x in gpx_data]

        lon_func = interp1d(x, lon, kind='linear')
        lat_func = interp1d(x, lat, kind='linear')

        alt_func = None
        if len(gpx_data[0]) > 3:
            alt = [x[3] for x in gpx_data]
            alt_func = interp1d(x, alt, kind='linear')

        # lon_func = interp1d(x, lon, kind='cubic')
        # lat_func = interp1d(x, lat, kind='cubic')
        # alt_func = interp1d(x, alt, kind='cubic')

        # lon_func = UnivariateSpline(line, lon)
        # lat_func = UnivariateSpline(line, lat)
        # alt_func = UnivariateSpline(line, alt)

        return lon_func, lat_func, alt_func

    def write_csv(self, head, data, geom_cols, geom_func, ouf_params):
        ouf_path = ouf_params[0]
        ouf_sep = ouf_params[1]
        ouf_cols = ouf_params[2]
        ouf_icols = [head.index(l) for l in ouf_cols]
        # print(ouf_icols)
        # c = [l for l in head if head.index(l) in ouf_icols]
        # print(c)

        with open(ouf_path, '+w') as ouf:
            new_head = [l for l in head[:-1] if head[:-1].index(l) in ouf_icols] + list(geom_cols)
            ouf.write(ouf_sep.join(new_head) + '\n')  # ['FIELD', 'qmc', 'st', 'TIME', 'LON', 'LAT', 'ALT']
            for line in data:
                try:
                    new_geom = [geom_func[0](line[-1]), geom_func[1](line[-1])]
                    if geom_func[2] is not None: new_geom.append(geom_func[2](line[-1]))
                except ValueError as e:
                    new_geom = [0, 0]
                    if geom_func[2] is not None: new_geom.append(0)

                try:
                    line[0] = int(line[0]) / 1000
                except Exception as e:
                    pass

                new_line = [l for l in line[:-1] if line[:-1].index(l) in ouf_icols] + new_geom
                # print(new_line)
                ouf.write(ouf_sep.join([str(s) for s in new_line]) + '\n')

        with open(ouf_path) as ouf:
            if len(ouf.readlines()) > 0:
                return f'Файл {ouf_params[0]} сохранен.'
            else: return f'Файл {ouf_params[0]} не сохранен.'
        # return

    def gps_binding(self, inf_params, gps_params, ouf_params):
        # input files
        fpaths = inf_params[0]
        inf_sep = inf_params[1]
        inf_time_cols = inf_params[2]
        inf_data_format = inf_params[3]

        # gps files
        gps_paths = gps_params[0]
        gps_sep = gps_params[1]
        gps_time_cols = gps_params[2]
        gps_data_format = gps_params[3]
        gps_geom_cols = gps_params[4]

        # output file
        ouf_path = ouf_params[0]
        ouf_sep = ouf_params[1]
        ouf_cols = ouf_params[2]

        head, data = self.read_csv(*inf_params)
        print('\nInput data', head, *data[:3], sep='\n')

        if all(item in [os.path.splitext(path)[1] for path in gps_paths] for item in ['.gpx']):
            gps_data = self.read_gpx(gps_paths)
            gps_geom_cols = ('LON', 'LAT', 'ALT')
            print('\nGPS as gpx', *gps_data[:3], sep='\n')
        else:
            ghead, gdata = self.read_csv(*gps_params[:-1])
            gps_data = self.get_gps_points(ghead, gdata, gps_geom_cols)
            print('\nGPS as csv', *gps_data[:3], sep='\n')

        if len(gps_data) > 0 and len(data) > 0:
            geom_func = self.get_interpolated_func(gps_data)
            m = self.write_csv(head, data, gps_geom_cols, geom_func, ouf_params)
            return m



if __name__ == '__main__':
    # fpaths = [
    #     '/Users/ronya/PycharmProjects/TESTDATA/Aunakit/Aunakit_Data/Magn_Aunakit/20210721/Data/2021-07-21_02-42-06.txt',
    #     '/Users/ronya/PycharmProjects/TESTDATA/Aunakit/Aunakit_Data/Magn_Aunakit/20210721/Data/2021-07-21_04-29-56.txt']
    # gpxs = ['/Users/ronya/PycharmProjects/TESTDATA/Aunakit/Aunakit_Data/Magn_Aunakit/20210721/LOG/00000001.BIN.gpx',
    #         '/Users/ronya/PycharmProjects/TESTDATA/Aunakit/Aunakit_Data/Magn_Aunakit/20210721/LOG/00000002.BIN.gpx']
    res_path = '/Users/ronya/PycharmProjects/TESTDATA/OUTPUT/output6.txt'
    #
    # m = GPSBuilder().gps_binding((fpaths), gpxs, res_path, '\t')

    # fpaths = ['/Users/ronya/PycharmProjects/TESTDATA/input/read_csv/' + 'test'+str(i)+'.txt' for i in range(1, 9)]
    # print(len(fpaths))

    # data = GPSBuilder().read_csv(fpaths,time_cols=('DATE', 'TIME'), onlyHead=False)
    # data = GPSBuilder().read_csv(fpaths, onlySep=True)
    # print(data[1])
    # print(data[2], *data[3], len(data[2]), len(data[3]), sep='\n')

    gps_paths = ['/Users/ronya/PycharmProjects/TESTDATA/input/read_gps_csv/20210830_f1-6.txt']
    gps_params = (gps_paths, '\t', ['TIME'], '%d-%m-%YT%H:%M:%S,%f',  ('LON', 'LAT'))
    i, m, ghead, gdata = GPSBuilder().read_csv(*gps_params[:-1])
    i, m, gps_data = GPSBuilder().get_gps_points(ghead, gdata, gps_params[-1])
    gps_func = GPSBuilder().get_interpolated_func(gps_data)
    print(i, m, ghead, *gdata[:10], sep='\n')
    print(i, m, ghead, *gps_data[:10], sep='\n')
    print(gps_func)
    i, m = GPSBuilder().write_csv(ghead, gdata, gps_func, (res_path, '\t', ('FIELD', 'TIME')))



