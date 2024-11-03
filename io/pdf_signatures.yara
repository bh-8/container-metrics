import "cm"

// rule hits whenever PDF magic number is found in a file
rule is_pdf {
    strings:
        $pdf_head = { 25 50 44 46 2D }
    condition:
        any of them
}

// rule hits when the corresponding pdf-section does not completely cover the file size
rule eof_appending : main {
    condition:
        is_pdf and cm.jmesq_i(mdb_url, mdb_pjt, mdb_set, mdb_oid, "data[?mime_type=='application/pdf'].[position,length] | [0] | sum(@)") < cm.jmesq_i(mdb_url, mdb_pjt, mdb_set, mdb_oid, "meta.file.size")
}

// rule hits whenever a specific copyright comment appears and there is specific stream content
rule pdfstego : main {
    strings:
        $copyright_comment = { 25 E2 E3 CF D3 0A }
    condition:
        is_pdf and #copyright_comment > 0 and @copyright_comment[1] == 9 and cm.jmesq_i(mdb_url, mdb_pjt, mdb_set, mdb_oid, "data[?mime_type=='text/plain'].content.uncovered[0].volatile_data | length([?(contains(@, '0.000 0.000 0.000 rg\\nBT\\n') && contains(@, '0.000 Tf\\n100.000 Tz\\n0.000 Tc\\n0.000\\n0.000\\nTd <') && contains(@, '> Tj\\nET\\n'))])") == 1
}

// signature consists of special copyright token
rule pdfhide : main {
    strings:
        $copyright_comment = { 25 BF F7 A2 FE 0A }
    condition:
        is_pdf and #copyright_comment > 0 and @copyright_comment[1] == 9
}

// rule searches for keywords and pdf version 1.3
rule boobytrappdf : main {
    strings:
        $copyright_comment = { 25 E2 E3 CF D3 0A }
        $sus_token1 = "/JavaScript"
        $sus_token2 = "/EmbeddedFiles"
    condition:
        is_pdf and #copyright_comment > 0 and @copyright_comment[1] == 9 and #sus_token1 > 0 and #sus_token2 > 0 and cm.jmesq_s(mdb_url, mdb_pjt, mdb_set, mdb_oid, "data[?mime_type=='application/pdf'].content.header[].version | [0]") == "1.3"
}
