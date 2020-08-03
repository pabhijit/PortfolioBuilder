from app import app
from app import cache
from flask import request

import os
import logging
import pandas as pd

_logger = logging.getLogger('__name__')


@app.route("/")
def index():
	return "Hello from Portfolio Builder"


@app.route("/universe")
def universe():

	args = request.args

	universe_type = args.get('type') if 'type' in args else None
		
	universe_date = args.get('date') if 'date' in args else None

	if universe_type is None or universe_date is None:
		return "Incomplete query string received", 200
	else:
		df_universe = load_universe(universe_type, universe_date)
		return df_universe.to_html()


@app.route("/carveout")
def carveout():

	args = request.args

	carveout_name = args.get('name') if 'name' in args else None
	carveout_type = args.get('type') if 'type' in args else None
	carveout_date = args.get('date') if 'date' in args else None
	carveout_filters = args.getlist('filters') if 'filters' in args else None

	if carveout_name is None or carveout_type is None or carveout_date is None or carveout_filters is None:
		return "Incomplete query string received", 200
	else:
		df_carveout = load_carveout(carveout_name, carveout_type, carveout_date, carveout_filters)

		return df_carveout.to_html()

@app.route("/returns")
def returns():


	args = request.args

	carveout_name = args.get('name') if 'name' in args else None
	carveout_date = args.get('date') if 'date' in args else None

	if carveout_name is None or carveout_date is None:
		return "Incomplete query string received", 400
	else:
		df_carveout = cache.get((carveout_name, carveout_date))
		if df_carveout is None:
			return "Carveout data does not exist", 400
		else:
			return str(df_carveout['weighted_return'].sum())

@cache.memoize(60)
def load_universe(universe_type, universe_date):

	print(f'Loading {universe_type} universe for date {universe_date}')

	universe_file = os.path.join(os.path.dirname(os.path.dirname(__file__)),
	                            'resources', universe_type, 'universe_' + universe_date + '.csv') 

	return pd.read_csv(universe_file)


def load_carveout(carveout_name, carveout_type, carveout_date, carveout_filters):

	print(f'Creating {carveout_type} index for date {carveout_date}')

	df_out = load_universe(carveout_type, carveout_date)

	for filter_str in carveout_filters:
		for filter_sub_str in filter_str.split(';'):
			print(f'Applying filter {filter_sub_str}')
			df_out.query(filter_sub_str, inplace=True)

	if not df_out.empty:
		df_out = calculate_weight(df_out)
		cache.set((carveout_name, carveout_date), df_out, timeout=300)

	return df_out


def calculate_weight(df_out):
	
	df_out['value'] = df_out['amount_outstanding'] * df_out['price']
	port_value = df_out['value'].sum()
	df_out['weight'] = df_out['value'] / port_value
	df_out['weighted_return'] = df_out['weight'] * df_out['returns']

	return df_out[['cusip', 'price', 'returns', 'weight', 'weighted_return']]


def normalize_query_param(value):
    """
    Given a non-flattened query parameter value,
    and if the value is a list only containing 1 item,
    then the value is flattened.

    :param value: a value from a query parameter
    :return: a normalized query parameter value
    """
    return value if len(value) > 1 else value[0]


def normalize_query(params):
    """
    Converts query parameters from only containing one value for each parameter,
    to include parameters with multiple values as lists.

    :param params: a flask query parameters data structure
    :return: a dict of normalized query parameters
    """
    params_non_flat = params.to_dict(flat=False)
    return {k: normalize_query_param(v) for k, v in params_non_flat.items()}


