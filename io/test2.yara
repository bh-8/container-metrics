import "console"
import "cm"

rule example_rule : main {
    condition:
        console.log("test.yara: Hello, World @ ", cm.jmesq_f("mongodb://admin:admin@mongo-db:27017", "2024-07-22", "test", mdb_oid, "sections[?mime_type=='application/pdf'].segments.header[].version | [0]"))
}
