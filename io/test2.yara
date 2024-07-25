import "console"
import "cm"

rule example_rule : main {
    condition:
        console.log("test2.yara: ", cm.jmesq_f(mdb_url, mdb_pjt, mdb_set, mdb_oid, "sections[?mime_type=='application/pdf'].segments.header[].version | [0]"))
}
