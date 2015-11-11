#!/Users/sdc50/Documents/_MyDocuments/CI-Water/code/venvs/tethys/bin/python
import urllib2
import netCDF4 as nc
import os
import time
import calendar


def main(urls_url, output_file_name):
    urls = urllib2.urlopen(urls_url).read().strip().split()
    combined_data_output = initialize_output_file(output_file_name)
    for index, url in enumerate(urls):
        data = download_data(url)
        append_data(data, combined_data_output)


def download_data(url):
    raw_data = urllib2.urlopen(url).read()
    tmp_file_name = 'tmp.nc'
    with open(tmp_file_name, 'w') as tmp:
        tmp.write(raw_data)
    data = nc.Dataset(tmp_file_name, 'r')
    os.remove(tmp_file_name)

    return data


def initialize_output_file(output_file_name):
    combined_data_output = nc.Dataset(output_file_name, 'w')

    combined_data_output.createDimension('time')

    time_var = combined_data_output.createVariable('time', 'i8', ('time',))
    time_var.long_name = 'time'
    time_var.calendar = 'gregorian'
    epoch = time.gmtime(0)
    time_var.units = time.strftime("seconds since %Y-%m-%d %H:%M:%S", epoch)

    return combined_data_output


def append_data(data_input, combined_data_output):
    variables = data_input.variables
    initialize = False
    for var_name in variables:
        copy_var = get_copied_variable(var_name, combined_data_output)
        if not copy_var:
            copy_all_variables(data_input, combined_data_output)
            initialize = True
            copy_var = get_copied_variable(var_name, combined_data_output)

        var = variables[var_name]
        dimensions = copy_var.dimensions
        if 'time' in dimensions:
            copy_variable_data_to_dataset(var, combined_data_output, True)
        elif initialize:
            copy_variable_data_to_dataset(var, combined_data_output)


def copy_variable_data_to_dataset(var, dataset, new_time_step=False):
    var_copy = get_copied_variable(var.name, dataset)
    if new_time_step:
        orig_num_dims = len(var.dimensions)
        time_step = add_time_step(var.initial_time, dataset.variables['time'])
        code_statment = "var_copy[%s, time_step] = var[:]" % (', '.join([':']*orig_num_dims),)
        exec(code_statment)
    else:
        var_copy[:] = var[:]


def add_time_step(time_str, time_var):
    ts = calendar.timegm( time.strptime(time_str, '%m/%d/%Y (%H:%M)'))
    try:
        step = time_var[:].tolist().index(ts)
    except (ValueError, IndexError),  e:
        step = len(time_var)
        time_var[step] = ts
    return step


def copy_all_variables(from_dataset, to_dataset):
    copy_all_dimensions(from_dataset, to_dataset)
    variables = from_dataset.variables
    for var_name in variables:
        var = variables[var_name]
        copy_variable(var, to_dataset)


def copy_all_dimensions(from_dataset, to_dataset):
    map_names(from_dataset)
    for dim_name in from_dataset.dimensions:
        dim = from_dataset.dimensions[dim_name]
        copy_dimension(dim, to_dataset)


def copy_variable(var, dataset):
    name  = get_remapped_name(var.name)
    if name in dataset.variables:       #this is the case for overlapping lat/lon variables
        return dataset.variables[name]
    else:
        data_type = var.dtype
        dimensions = [get_remapped_name(n) for n in var.dimensions]
        if is_gridded_data(dimensions):
            dimensions.append('time')

        copy_var = dataset.createVariable(name, data_type, dimensions)
        for attr in var.ncattrs():
                copy_var.setncattr(attr, var.getncattr(attr))
        return copy_var


def get_copied_variable(var_name, dataset):
    try:
        return dataset.variables[get_remapped_name(var_name)]
    except KeyError, e:
        return None


def is_gridded_data(dimensions):
    if LAT_NAME in dimensions and LON_NAME in dimensions:
        return True
    else:
        return False


def copy_dimension(dim, dataset):
    if dim.isunlimited():
        size = None
    else:
        size = len(dim)

    name = get_remapped_name(dim.name)
    if name not in dataset.dimensions:
        dataset.createDimension(name, size)


LAT_UNITS = ['degrees_north', 'degree_north', 'degree_N', 'degrees_N', 'degreeN', 'degreesN']
LON_UNITS = ['degrees_east', 'degree_east', 'degree_E', 'degrees_E', 'degreeE', 'degreesE']
LAT_NAME = 'lat'
LON_NAME = 'lon'
name_map = {}

def map_names(dataset):
    variables = dataset.variables
    lat, lon = get_lat_lon_variables(variables)
    if lat:
        remap_name(lat, LAT_NAME)
    if lon:
        remap_name(lon, LON_NAME)


def remap_name(var, name):
    dim = var.dimensions[0]
    name_map[dim] = name
    name_map[var.name] = name


def get_remapped_name(name):
    if name in name_map.keys():
        return name_map[name]
    else:
        return name


def get_lat_lon_variables(variables):
    lat_var = None
    lon_var = None

    for var_name in variables:
        var = variables[var_name]
        units = get_variable_units(var)
        if units in LON_UNITS:
            lon_var =  var
        elif units in LAT_UNITS:
            lat_var = var

    return lat_var, lon_var


def get_variable_units(variable):
    if 'units' in variable.ncattrs():
        return variable.units


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 2:
        urls_url = sys.argv[1]
        output_file_name = sys.argv[2]

    #urls_url = 'http://disc.gsfc.nasa.gov/SSW/WWW-TMP/SSW_download_2015-09-09T20:23:55_26084_RLoU9CAU.inp' #1 month 1 var
    #urls_url = 'http://disc.gsfc.nasa.gov/SSW/WWW-TMP/SSW_download_2015-09-10T16:12:10_52615_76rBuSEc.inp' #1 day 2 vars from 2 datasets
    #urls_url = 'http://disc.gsfc.nasa.gov/SSW/WWW-TMP/SSW_download_2015-09-11T17:09:06_13144_RXrnSxs9.inp' #1 month 3 vars from 2 datasets
    #output_file_name = 'nldas_data.nc'

    if urls_url and output_file_name:
        start = time.time()
        main(urls_url, output_file_name)
        delta_time = (time.time() - start)/60
        print "time [min]: %.2f" % (delta_time,)



