from custom.filesystem_functions import print_path, get_path

file = get_path(r"")
dir = get_path(r"")

# print(file)
print_path(file.path)

# print(dir)
# print_path(dir.path)

# types:
#  movies
#  tvshows
#  ...
class Movie:
    name: str
    year: str

class TvShow:
    name: str
    start_year: str
    end_year: str

# check naming based on type
# movies = title [year]
# tvshows = title[yearto-year]
# ...

