README
~~~~~~~

Note: there is a bug in images2gif which you must fix manually
you must find

    `for im in images:
        palettes.append( getheader(im)[1] )`
    replace with

    `for im in images:
        palettes.append(im.palette.getdata()[1])`
