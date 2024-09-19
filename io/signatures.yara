import "console"
import "math"
import "cm"

// rule hits whenever JPEG magic number is found at the beginning of a file
rule is_jpeg {
    strings:
        $jpeg_magic_number = { FF D8 }
    condition:
        #jpeg_magic_number > 0 and @jpeg_magic_number[1] == 0
}

// rule hits whenever MP3 magic number is found at the beginning of a file
rule is_mp3 {
    strings:
        $mpeg_sync_word = { FF (F? | E?) }
        $id3v2_header = { 49 44 33 }
    condition:
        (#id3v2_header > 0 and @id3v2_header[1] == 0 and #mpeg_sync_word > 0) or (#mpeg_sync_word > 0 and @mpeg_sync_word[1] == 0)
}

// rule hits whenever PDF magic number is found in a file
rule is_pdf {
    strings:
        $pdf_head = { 25 50 44 46 2D }
    condition:
        any of them
}

// rule fires whenever a mp3 file is encoded using a constant bitrate
rule is_mp3_cbr {
    condition:
        cm.jmesq_s(mdb_url, mdb_pjt, mdb_set, mdb_oid, "(data[?mime_type=='audio/mpeg'].content.mpeg_frames[].header.bitrate | min(@)) == (data[?mime_type=='audio/mpeg'].content.mpeg_frames[].header.bitrate | max(@))") == "true"
}

rule is_mp3_vbr {
    condition:
        not is_mp3_cbr
}

////////////////////////////////////////////////////////////////////////////////////////////////////

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

// mp3stego
rule mp3stego : main {
    condition:
        is_mp3 and is_mp3_cbr and cm.jmesq_s(mdb_url, mdb_pjt, mdb_set, mdb_oid, "(data[?mime_type=='audio/mpeg'].content.mpeg_frames[].[offset,length] | [-1:][] | sum(@)) > meta.file.size") == "true"
}

rule mp3stego_derivative : main {
    condition:
        // "avg(map(&((@ - avg($)) * (@ - avg($))), @))" berechnet standardabweichung: ABER: in Regel kann $ nicht genutzt werden; es fehlt Zugriff auf parent-node; $ ist Root-Node, @ ist Current-Node!
        is_mp3 and is_mp3_cbr and console.log("mp3stego_derivative_abs = ", cm.jmesq_s(mdb_url, mdb_pjt, mdb_set, mdb_oid, "data[?mime_type=='audio/mpeg'].content.mpeg_frames[].[side_info.granule_info[0].part2_3_length,side_info.granule_info[1].part2_3_length] | map(&[], @) | zip(@[0:-1], @[1:]) | map(&zip(@[0], @[1]), @) | map(&map(&(@[1] - @[0]), @), @) | [] | [sum(map(&abs(@), @[:512:1])), sum(map(&abs(@), @[:-513:-1])), ((sum(map(&abs(@), @[:512:1]))) / (sum(map(&abs(@), @[:-513:-1]))))]")) and cm.jmesq_f(mdb_url, mdb_pjt, mdb_set, mdb_oid, "data[?mime_type=='audio/mpeg'].content.mpeg_frames[].[side_info.granule_info[0].part2_3_length,side_info.granule_info[1].part2_3_length] | map(&[], @) | zip(@[0:-1], @[1:]) | map(&zip(@[0], @[1]), @) | map(&map(&(@[1] - @[0]), @), @) | [] | ((sum(map(&abs(@), @[:512:1]))) / (sum(map(&abs(@), @[:-513:-1]))))") > 6
}

// mp3stegz-manipulated files can be recognized by the sequence 'XXXX' right after the side info field of the first manipulated frame
rule mp3stegz : main {
    strings:
        $mp3stegz_signature = { FF (F? | E?) [34] 58 58 58 58 }
    condition:
        is_mp3 and #mp3stegz_signature > 0
}

// stegonaut-manipulated files can be recognized by looking at 5 specific bits in the first mpeg frame
rule stegonaut : main {
    strings:
        $mpeg_sync_word = { FF FB }
    condition:
        is_mp3 and (uint8(@mpeg_sync_word[1] + 2) & 0x0000000000000001) == 1 and (uint8(@mpeg_sync_word[1] + 3) & 0x000000000000000F) == 15
}

rule pdfstego : main {
    condition:
        is_pdf and cm.jmesq_i(mdb_url, mdb_pjt, mdb_set, mdb_oid, "data[?mime_type=='text/plain'].content.uncovered[0].volatile_data | length([?(contains(@, '0.000 0.000 0.000 rg\\nBT\\n') && contains(@, '0.000 Tf\\n100.000 Tz\\n0.000 Tc\\n0.000\\n0.000\\nTd <') && contains(@, '> Tj\\nET\\n'))])") == 1
}

rule openpuff_pdf : main {
    strings:
        $lf = { 0A }
        $cr = { 0D }
    condition:
        is_pdf and #lf > 0 and #cr > 0 and console.log("openpuff_pdf (if value is greater than 10!?) = ", math.abs(#lf - #cr))
}
