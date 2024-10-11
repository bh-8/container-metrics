import "console"
import "cm"

// rule hits whenever MP3 magic number is found at the beginning of a file
rule is_mp3 {
    strings:
        $mpeg_sync_word = { FF (F? | E?) }
        $id3v2_header = { 49 44 33 }
    condition:
        (#id3v2_header > 0 and @id3v2_header[1] == 0 and #mpeg_sync_word > 0) or (#mpeg_sync_word > 0 and @mpeg_sync_word[1] == 0)
}

// rule fires whenever a mp3 file is encoded using a constant bitrate
rule is_mp3_cbr {
    condition:
        cm.jmesq_s(mdb_url, mdb_pjt, mdb_set, mdb_oid, "(data[?mime_type=='audio/mpeg'].content.mpeg_frames[].header.bitrate | min(@)) == (data[?mime_type=='audio/mpeg'].content.mpeg_frames[].header.bitrate | max(@))") == "true"
}

// mp3steganography-lib
rule mp3stegolib : main {
    condition:
        is_mp3 and cm.jmesq_i(mdb_url, mdb_pjt, mdb_set, mdb_oid, "data[?mime_type=='audio/mpeg'].content.mpeg_frames[0].side_info.granule_info[].part2_3_length[] | [0]") == 3056
}

// mp3stego leaves traces in part2_3_length values; rule uses 1st derivative of those values to determine whether a manipulation can be assumed
rule mp3stego_derivative {
    condition:
        is_mp3 and cm.jmesq_f(mdb_url, mdb_pjt, mdb_set, mdb_oid, "data[?mime_type=='audio/mpeg'].content.mpeg_frames[].[side_info.granule_info[0].part2_3_length,side_info.granule_info[1].part2_3_length] | map(&[], @) | zip(@[0:-1], @[1:]) | map(&zip(@[0], @[1]), @) | map(&map(&(@[1] - @[0]), @), @) | [] | ((sum(map(&abs(@), @[:512:1]))) / (sum(map(&abs(@), @[:-513:-1]))))") > 4.8
}
rule mp3stego : main {
    condition:
        is_mp3 and is_mp3_cbr and mp3stego_derivative and cm.jmesq_s(mdb_url, mdb_pjt, mdb_set, mdb_oid, "(data[?mime_type=='audio/mpeg'].content.mpeg_frames[].[offset,length] | [-1:][] | sum(@)) > meta.file.size") == "true"
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

// stegonaut-manipulated files can be recognized by checking private header bits
rule tamp3r : main {
    condition:
        is_mp3 and cm.jmesq_s(mdb_url, mdb_pjt, mdb_set, mdb_oid, "data[?mime_type=='audio/mpeg'].content.mpeg_frames[].header.private | map(&to_string(@), @) | [length([@ | [?@ == 'true']] | []), length([@ | [?@ == 'false']] | [])] | (@[0] > to_number('8')) && (@[1] > to_number('8'))") == "true"
}
