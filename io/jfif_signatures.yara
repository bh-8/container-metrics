import "console"
import "cm"

// rule hits whenever JPEG magic number is found at the beginning of a file
rule is_jpeg {
    strings:
        $jpeg_magic_number = { FF D8 }
    condition:
        #jpeg_magic_number > 0 and @jpeg_magic_number[1] == 0
}

// f5-manipulated images feature of a very specific quantization table
rule f5 : main {
    strings:
        $f5_signature = { FF DB 00 84 00 06 04 05 06 05 04 06 06 05 06 07 07 06 08 0A 10 0A 0A 09 09 0A 14 0E 0F 0C 10 17 14 18 18 17 14 16 16 1A 1D 25 1F 1A 1B 23 1C 16 16 20 2C 20 23 26 27 29 2A 29 19 1F 2D 30 2D 28 30 25 28 29 28 01 07 07 07 0A 08 0A 13 0A 0A 13 28 1A 16 1A 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 28 }
    condition:
        is_jpeg and #f5_signature > 0
}

// jsteg-manipulated images are lacking the APP0 segment, which is usually very common
rule jsteg : main {
    strings:
        $expected_structure = { FF D8 [-] FF E0 [-] FF DA [-] FF D9 }
    condition:
        is_jpeg and #expected_structure == 0
}
