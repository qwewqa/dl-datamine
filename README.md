# dragalia-wiki-scripts

## Requirements
* Python 3
* Pillow (https://pypi.org/project/Pillow/)

## Example usage
```
Process_DL_Images.py -i <input_folder> -o <output_folder>
```
To remove the old output folder before processing:
```
Process_DL_Images.py -i <input_folder> -o <output_folder> --delete_old
```

### Enemy Data parsing
A standalone script, but also run as part of Process_DL_Data.
```
Enemy_Parser.py -i <input_folder> -o <output_folder>
```
To specify what directory to find the ManualMapRelations.txt file in:
```
Enemy_Parser.py -i <input_folder> -o <output_folder> -map <map_file_folder>
```