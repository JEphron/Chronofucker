README

Note: This project requires images2gif. There is a bug in images2gif.py which you must fix manually.

You must find

    for im in images:
        palettes.append( getheader(im)[1] )
and replace it with

    for im in images:
        palettes.append(im.palette.getdata()[1])
