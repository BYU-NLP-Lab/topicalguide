#!/bin/bash
# This will compile Snowball, then compile the .sbl file defining the stemmer

# Define the path to your .sbl file.
SBL=stem_ISO_8859_1.sbl

gcc -O -o Snowball snowball_code/compiler/*.c
./Snowball $SBL -o lang/language -ep H_ -utf8
gcc -o "stemmer" lang/*.c
echo "Done"







