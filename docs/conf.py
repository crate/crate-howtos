from crate.theme.rtd.conf.crate_howtos import *

linkcheck_ignore = [
    # Server not available on 2023-11-16.
    r"https://.+\.r-project.org/.*",
    # Forbidden by WordPress
    "https://crate.io/wp-content/uploads/2018/11/copy_from_population_data.zip",
    r'http://localhost:\d+/',
]

if "sphinx.ext.intersphinx" not in extensions:
    extensions += ["sphinx.ext.intersphinx"]

if "intersphinx_mapping" not in globals():
    intersphinx_mapping = {}

intersphinx_mapping.update({
    'matplotlib': ('https://matplotlib.org/stable/', None),
    'pandas': ('https://pandas.pydata.org/pandas-docs/stable/', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    })
