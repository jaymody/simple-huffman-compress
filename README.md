Simple huffman encoding based file compression.

It's really slow, doesn't compress things that much, but hey, it's simple and it works.

Requires `Python 3.12` or better:

```bash
python3.12 compress.py compress original.txt compressed.txt
python3.12 compress.py decompress compressed.txt decompressed.txt
```

Compressing the source code itself we have (wow, very meta):

```bash
# compress into compressed_file
python3.12 compress.py compress compress.py compressed_file

# decompress into decompressed_file
python3.12 compress.py decompress compressed_file decompressed_file

# ensure that original file = recovered file
diff compress.py decompressed_file

# compression ratio (higher is better)
echo "scale=4;$(wc -c <compress.py)/$(wc -c <compressed_file)" | bc
```

Which gives a compression ratio of `1.5464` (that, is the compressed file is about 65% of the size of the original file).
